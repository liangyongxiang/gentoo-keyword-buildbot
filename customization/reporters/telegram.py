
from twisted.internet import defer
import buildbot.reporters.telegram as telegram

class CustomTelegramContact(telegram.TelegramContact):

    def __init__(self, user, channel=None):
        super().__init__(user, channel)

    def getSchedulerByName(self, name):
        schedulers = self.master.scheduler_manager.namedServices
        if name not in schedulers:
            raise ValueError(f"unknown triggered scheduler: {repr(name)}")
        return schedulers[name]

    @defer.inlineCallbacks
    def command_ZBT(self, args, **kwargs):
        try:
            argv = self.splitArgs(args)
            package = argv[0]
            scheduler = self.getSchedulerByName('zbt-force')
            yield self.send(f'zbt {package}')
            yield scheduler.force(owner=self.describeUser(), package=package)
        except IndexError:
            self.send("Which package do you want to force test?")
        return
    command_ZBT.usage = "zbt dump package list than run tatt"

    @defer.inlineCallbacks
    def command_TATT(self, args, **kwargs):
        try:
            argv = self.splitArgs(args)
            bugid = argv[0]
            scheduler = self.getSchedulerByName('tatt-force')
            yield self.send(f'tatt -b {bugid}')
            yield scheduler.force(owner=self.describeUser(), bugid=bugid)
        except IndexError:
            self.send("Which bugid do you want to force test?")
        return
    command_TATT.usage = "tatt with bugid"

telegram.TelegramStatusBot.contactClass = CustomTelegramContact

