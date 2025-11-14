from ok import TriggerTask, Logger, og
from src.scene.DNAScene import DNAScene
from src.tasks.BaseDNATask import BaseDNATask
from src.tasks.BaseListenerTask import BaseListenerTask

from pynput import mouse

logger = Logger.get_logger(__name__)


class TriggerDeactivateException(Exception):
    """停止激活异常。"""
    pass


class AutoMoveTask(BaseListenerTask, BaseDNATask, TriggerTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "自动穿引共鸣"
        self.description = "需主动激活，运行中也可使用左键打断"
        self.scene: DNAScene | None = None
        self.setup_listener_config()
        self.default_config.update({
            '按下时间': 0.50,
            '间隔时间': 0.45,
        })
        self.config_description.update({
            '按下时间': '左键按住多久',
            '间隔时间': '左键释放后等待多久',
        })
        self.manual_activate = False
        self.signal = False
        self.signal_interrupt = False
        self.is_down = False

    def disable(self):
        """禁用任务时，断开信号连接。"""
        self.try_disconnect_listener()
        return super().disable()
    
    def enable(self):
        """启用任务时，信号连接。"""
        self.reset()
        self.try_connect_listener()
        return super().enable()

    def reset(self):
        self.manual_activate = False
        self.signal = False
        self.signal_interrupt = False

    def run(self):
        if self.signal:
            self.signal = False
            if not self.scene.in_team(self.in_team_and_world):
                return
            if og.device_manager.hwnd_window.is_foreground():
                self.switch_state()

        while self.manual_activate:
            try:
                self.do_move()
            except TriggerDeactivateException as e:
                logger.info(f'auto_move_task_deactivate {e}')
                break
            
        if self.is_down:
            self.is_down = False
            self.mouse_up()

    def do_move(self):
        self.mouse_down()
        self.is_down = True
        self.sleep_check(self.config.get('按下时间', 0.50), False)
        self.mouse_up()
        self.is_down = False
        self.sleep_check(self.config.get('间隔时间', 0.45))

    def sleep_check(self, sec, check_signal_flag=True):
        remaining = sec
        step = 0.1
        while remaining > 0:
            s = step if remaining > step else remaining
            self.sleep(s)
            remaining -= s
            if not (self.signal_interrupt or
                    (check_signal_flag and self.signal) or
                    not self.scene.in_team(self.in_team_and_world)):
                continue
            self.switch_state()
            if not self.manual_activate:
                raise TriggerDeactivateException()

    def switch_state(self):
        self.signal_interrupt = False
        self.signal = False
        self.manual_activate = not self.manual_activate
        if self.manual_activate:
            logger.info("激活快速移动")
        else:
            logger.info("关闭快速移动")

    def on_global_click(self, x, y, button, pressed):
        if self._executor.paused:
            return
        if self.config.get('激活键', 'x2') == '使用键盘':
            if button not in (mouse.Button.left,):
                return
        if self.config.get('激活键', 'x2') == 'x1':
            btn = mouse.Button.x1
        else:
            btn = mouse.Button.x2
        if pressed:
            if button == btn:
                self.signal = True
            elif button == mouse.Button.left and self.manual_activate:
                self.signal_interrupt = True

    def on_global_press(self, key):
        if self._executor.paused or self.config.get('激活键', 'x2') != '使用键盘':
            return
        lower = self.config.get('键盘', 'ctrl_r').lower()
        hot_key = self.normalize_hotkey(lower)
        if self.key_equal(key, hot_key):
            self.signal = True
