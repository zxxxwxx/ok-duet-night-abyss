from qfluentwidgets import FluentIcon
import time

from ok import Logger, TaskDisabledException
from src.tasks.BaseCombatTask import BaseCombatTask
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.CommissionsTask import CommissionsTask

logger = Logger.get_logger(__name__)


class AutoSkill(DNAOneTimeTask, CommissionsTask, BaseCombatTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "自动释放技能"

        self.default_config.update({
            '主画面侦测': True,
        })

        self.setup_commission_config()
        keys_to_remove = ["委托手册", "启用自动穿引共鸣", "自动选择首个密函和密函奖励", "优先选择持有数为0的密函奖励"]
        for key in keys_to_remove:
            self.default_config.pop(key, None)

        self.config_description.update({
            '主画面侦测': '如果不在可操控角色的画面则结束任务',
            '超时时间': '超时后将发出提示',
        })

        self.action_timeout = 10

    def run(self):
        DNAOneTimeTask.run(self)
        try:
            return self.do_run()
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error('AutoCombatSkill error', e)
            raise

    def do_run(self):
        self.load_char()
        _skill_time = 0
        self.wait_until(self.in_team, time_out=30)
        while True:
            if self.in_team():
                _skill_time = self.use_skill(_skill_time)
            else:
                if self.config.get('主画面侦测', False):
                    self.log_info_notify('任务完成')
                    self.soundBeep()
                    return
            if time.time() - self.start_time >= self.config.get('超时时间', 120):
                self.log_info_notify('任务超时')
                self.soundBeep()
                return
            self.sleep(0.2)
