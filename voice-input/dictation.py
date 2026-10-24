#!/usr/bin/env python3
"""Local Russian dictation on Intel NPU, controlled over a private Unix socket."""
import fcntl, json, logging, os, pathlib, signal, socket, struct, subprocess, sys, threading, time, wave
ROOT = pathlib.Path.home()/'.local/share/honor-dictation'
CACHE = pathlib.Path.home()/'.cache/honor-dictation'
RUNTIME = pathlib.Path(os.environ['XDG_RUNTIME_DIR'])/'honor-dictation'
SOCKET = RUNTIME/'control.sock'
MAX_SECONDS = 120
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, timeout=10, **kwargs)

def notify(title, body='', urgent=False):
    subprocess.run(['notify-send','-a','Голосовой ввод','-h','string:x-canonical-private-synchronous:honor-dictation',
                    '-u','critical' if urgent else 'normal','-t','6000',title,body], capture_output=True)

def focused():
    try:return json.loads(run(['niri','msg','-j','focused-window'],text=True).stdout) or {}
    except Exception:return {}

class PasteKeyboard:
    """Write-only virtual keyboard: inject the paste shortcut, never read real input."""
    def __init__(self):
        self.fd=os.open('/dev/uinput',os.O_WRONLY|os.O_NONBLOCK)
        fcntl.ioctl(self.fd,0x40045564,1)  # UI_SET_EVBIT / EV_KEY
        for key in range(1,256):fcntl.ioctl(self.fd,0x40045565,key)
        device=struct.pack('80sHHHHI',b'Honor Dictation Paste',6,1,0xd1c7,1,0)+bytes(1024)
        os.write(self.fd,device);fcntl.ioctl(self.fd,0x5501)  # UI_DEV_CREATE
        time.sleep(.5)
    def event(self,code,value):
        os.write(self.fd,struct.pack('llHHi',0,0,1,code,value))
        os.write(self.fd,struct.pack('llHHi',0,0,0,0,0));time.sleep(.02)
    def paste(self,terminal=False):
        # Linux key codes: left Ctrl=29, left Shift=42, V=47. No Enter.
        self.event(29,1)
        if terminal:self.event(42,1)
        try:self.event(47,1);self.event(47,0)
        finally:
            if terminal:self.event(42,0)
            self.event(29,0)
    def close(self):
        if self.fd is not None:
            fcntl.ioctl(self.fd,0x5502);os.close(self.fd);self.fd=None

class Dictation:
    def __init__(self):
        self.lock=threading.RLock(); self.engine_lock=threading.Lock()
        self.pipe=None; self.phase='idle'; self.recorder=None; self.started=0; self.target={}; self.error=None; self.bluetooth_profile=None; self.keyboard=None
        self.audio=RUNTIME/'recording.wav'
        threading.Thread(target=self.warm,daemon=True).start()
    def engine(self):
        with self.engine_lock:
            if self.pipe is None:
                import openvino as ov
                import openvino_genai as genai
                core=ov.Core()
                if 'NPU' not in core.available_devices:
                    raise RuntimeError('NPU недоступен. Проверьте права /dev/accel/accel0 и группу render.')
                CACHE.mkdir(parents=True,exist_ok=True)
                logging.info('Loading Whisper on NPU')
                self.pipe=genai.WhisperPipeline(str(ROOT/'model'),'NPU',CACHE_DIR=str(CACHE))
                logging.info('Whisper ready on NPU')
            return self.pipe
    def warm(self):
        try:self.engine(); self.error=None
        except Exception as e:
            self.error=str(e); logging.exception('NPU initialization failed')
            notify('Голосовой ввод: ошибка NPU',str(e)[:220],True)
    def status(self):
        with self.lock:return {'phase':self.phase,'device':'NPU','model_loaded':self.pipe is not None,'error':self.error}
    def toggle(self):
        with self.lock:
            if self.phase=='recording':
                self.finish();return self.status()
            if self.phase!='idle':
                notify('Идёт распознавание','Дождитесь текста; Ctrl+Super+Esc отменяет вставку.')
                return self.status()
            if self.error:
                notify('Голосовой ввод не готов',self.error[:220],True);return self.status()
            source=run(['pactl','get-default-source'],text=True).stdout.strip()
            if run(['pactl','get-source-mute',source],text=True,env=dict(os.environ,LC_ALL='C')).stdout.strip().endswith('yes'):
                notify('Микрофон выключен','Включите текущий микрофон в Noctalia и повторите сочетание.',True)
                return self.status()
            self.prepare_bluetooth(source)
            self.target=focused();self.started=time.monotonic();self.audio.unlink(missing_ok=True)
            self.recorder=subprocess.Popen(['pw-record','--rate','16000','--channels','1','--format','s16',
                                           '--media-role','Communication','--target',source,str(self.audio)],
                                          stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            self.phase='recording';self.cancelled=False
            notify('● Запись голоса','Говорите. Ctrl+Super+R — закончить; Ctrl+Super+Esc — отменить.')
            logging.info('Recording started')
            return self.status()
    def prepare_bluetooth(self, source):
        sources=json.loads(run(['pactl','-f','json','list','sources'],text=True).stdout)
        props=next((s.get('properties',{}) for s in sources if s.get('name')==source),{})
        card_name=props.get('device.name','')
        if not card_name.startswith('bluez_card.'):return
        cards=json.loads(run(['pactl','-f','json','list','cards'],text=True).stdout)
        card=next((c for c in cards if c['name']==card_name),None)
        if not card:return
        original=card['active_profile'];profiles=card['profiles']
        if profiles.get(original,{}).get('sources',0):return
        candidates=[(p['priority'],name) for name,p in profiles.items() if p.get('available') and p.get('sources',0)]
        if not candidates:raise RuntimeError('У выбранной Bluetooth-гарнитуры нет доступного режима микрофона.')
        profile=max(candidates)[1]
        run(['pactl','set-card-profile',card_name,profile])
        self.bluetooth_profile=(card_name,original,profile)
        time.sleep(.8)
        logging.info('Bluetooth recording profile activated')
    def restore_bluetooth(self):
        if self.bluetooth_profile:
            card,original,temporary=self.bluetooth_profile;self.bluetooth_profile=None
            try:
                cards=json.loads(run(['pactl','-f','json','list','cards'],text=True).stdout)
                current=next((c['active_profile'] for c in cards if c['name']==card),None)
                if current==temporary:run(['pactl','set-card-profile',card,original])
            except Exception:logging.exception('Could not restore Bluetooth profile')
    def stop_recorder(self):
        if self.recorder:
            if self.recorder.poll() is None:self.recorder.send_signal(signal.SIGINT)
            try:_,stderr=self.recorder.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self.recorder.kill();_,stderr=self.recorder.communicate()
            code=self.recorder.returncode;self.recorder=None
            self.restore_bluetooth()
            if code not in (0,-signal.SIGINT):
                # pw-record can return a nonzero code after SIGINT even with a finalized WAV.
                if not self.audio.exists() or self.audio.stat().st_size <= 44:
                    raise RuntimeError('Не удалось записать микрофон: '+stderr.decode(errors='replace')[:180])
                logging.info('Recorder exit=%s; validating captured WAV',code)
    def finish(self):
        self.phase='transcribing'
        try:self.stop_recorder()
        except Exception:
            self.phase='idle';self.audio.unlink(missing_ok=True);raise
        notify('Распознаю речь…','Локально на NPU. Первое распознавание может занять больше времени.')
        threading.Thread(target=self.transcribe,daemon=True).start()
    def transcribe(self):
        try:
            import numpy as np
            with wave.open(str(self.audio),'rb') as wav:
                if (wav.getframerate(),wav.getnchannels(),wav.getsampwidth()) != (16000,1,2):
                    raise RuntimeError('Некорректный формат записи')
                samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.float32)/32768.0
            self.audio.unlink(missing_ok=True)
            logging.info('Captured audio: %d samples, RMS %.6f',len(samples),float(np.sqrt(np.mean(samples*samples))) if len(samples) else 0)
            if len(samples)<6400 or float(np.sqrt(np.mean(samples*samples)))<0.002:
                notify('Речь не слышна','Проверьте выбранный микрофон и попробуйте ещё раз.');return
            t=time.monotonic()
            result=self.engine().generate(samples.tolist(),language='<|ru|>',task='transcribe',max_new_tokens=448)
            text=' '.join(str(result).split()).strip()
            logging.info('Transcription finished: %.2f seconds, %d characters',time.monotonic()-t,len(text))
            with self.lock:
                if self.cancelled:return
                if not text:
                    notify('Текст не распознан','Попробуйте ещё раз.');return
                # Keep the transcript in the clipboard for manual recovery; never send Enter.
                # wl-copy forks a persistent owner. Do not capture its inherited output pipes.
                subprocess.run(['wl-copy','--type','text/plain;charset=utf-8'],input=text.encode(),
                               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=5)
                current=focused()
                if not self.target.get('id') or current.get('id')!=self.target['id']:
                    notify('Текст скопирован','Активное окно изменилось. Вставьте текст вручную.');return
                terminal=any(s in str(current.get('app_id','')).lower() for s in ('kitty','foot','alacritty','wezterm','org.gnome.console'))
                if self.keyboard is None:self.keyboard=PasteKeyboard()
                self.keyboard.paste(terminal)
                notify('Текст вставлен','Запись удалена. Сообщение не отправлено.')
        except Exception as e:
            logging.exception('Dictation failed');notify('Ошибка голосового ввода',str(e)[:240],True)
        finally:
            self.audio.unlink(missing_ok=True)
            with self.lock:self.phase='idle'
    def cancel(self):
        with self.lock:
            self.cancelled=True
            if self.phase=='recording':self.stop_recorder();self.phase='idle'
            if self.phase!='transcribing':self.audio.unlink(missing_ok=True)
            notify('Голосовой ввод отменён','Текст не будет вставлен.')
            return self.status()
    def tick(self):
        with self.lock:
            if self.phase=='recording' and time.monotonic()-self.started>=MAX_SECONDS:self.finish()

def serve():
    RUNTIME.mkdir(mode=0o700,exist_ok=True);SOCKET.unlink(missing_ok=True)
    server=socket.socket(socket.AF_UNIX);server.bind(str(SOCKET));server.listen(4);server.settimeout(.5)
    state=Dictation()
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        while True:
            state.tick()
            try:conn,_=server.accept()
            except socket.timeout:continue
            with conn:
                conn.settimeout(2)
                try:
                    command=conn.recv(1024).decode().strip()
                    if command=='toggle':result=state.toggle()
                    elif command=='cancel':result=state.cancel()
                    elif command=='status':result=state.status()
                    else:raise ValueError('Unknown command')
                    conn.sendall(json.dumps(result).encode())
                except Exception as e:
                    logging.exception('Control failed');notify('Ошибка голосового ввода',str(e)[:200],True)
                    conn.sendall(json.dumps({'error':str(e)}).encode())
    finally:
        state.cancel()
        if state.keyboard is not None:state.keyboard.close()
        server.close();SOCKET.unlink(missing_ok=True)

def client(command):
    if not SOCKET.exists():run(['systemctl','--user','start','honor-dictation.service'])
    for _ in range(50):
        connection=socket.socket(socket.AF_UNIX)
        try:connection.connect(str(SOCKET));break
        except (FileNotFoundError,ConnectionRefusedError):connection.close();time.sleep(.1)
    else:raise RuntimeError('Служба голосового ввода не запустилась')
    with connection:
        connection.settimeout(10);connection.sendall(command.encode());print(connection.recv(16384).decode())

if __name__=='__main__':
    if sys.argv[1:]==['serve']:serve()
    else:client(sys.argv[1] if len(sys.argv)>1 else 'toggle')
