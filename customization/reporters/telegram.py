
from twisted.internet import defer
from buildbot.reporters.telegram import *
#from buildbot import config

class CustomTelegramContact(TelegramContact):

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

class CustomTelegramWebhookBot(TelegramWebhookBot):
    name = "CustomTelegramWebhookBot"
    contactClass = CustomTelegramContact

class CustomTelegramPollingBot(TelegramPollingBot):
    name = "CustomTelegramPollingBot"
    contactClass = CustomTelegramContact

TelegramPollingBot = CustomTelegramPollingBot
TelegramWebhookBot = CustomTelegramWebhookBot

class CustomTelegramBot(TelegramBot):
    name = "CustomTelegramBot"

    @defer.inlineCallbacks
    def reconfigService(self, bot_token, chat_ids=None, authz=None,
                        bot_username=None, tags=None, notify_events=None,
                        showBlameList=True, useRevisions=False,
                        useWebhook=False, certificate=None,
                        pollTimeout=120, retryDelay=30):
        print("TelegramBot: reconfigService")
        # need to stash these so we can detect changes later
        self.bot_token = bot_token
        if chat_ids is None:
            chat_ids = []
        self.chat_ids = chat_ids
        self.authz = authz
        self.useRevisions = useRevisions
        self.tags = tags
        if notify_events is None:
            notify_events = set()
        self.notify_events = notify_events
        self.useWebhook = useWebhook
        self.certificate = certificate
        self.pollTimeout = pollTimeout
        self.retryDelay = retryDelay

        # This function is only called in case of reconfig with changes
        # We don't try to be smart here. Just restart the bot if config has
        # changed.

        http = yield self._get_http(bot_token)

        if self.bot is not None:
            self.removeService(self.bot)

        if not useWebhook:
            self.bot = TelegramPollingBot(bot_token, http, chat_ids, authz,
                                          tags=tags, notify_events=notify_events,
                                          useRevisions=useRevisions,
                                          showBlameList=showBlameList,
                                          poll_timeout=self.pollTimeout,
                                          retry_delay=self.retryDelay)
        else:
            self.bot = TelegramWebhookBot(bot_token, http, chat_ids, authz,
                                          tags=tags, notify_events=notify_events,
                                          useRevisions=useRevisions,
                                          showBlameList=showBlameList,
                                          retry_delay=self.retryDelay,
                                          certificate=self.certificate)
        if bot_username is not None:
            self.bot.nickname = bot_username
        else:
            yield self.bot.set_nickname()
            if self.bot.nickname is None:
                raise RuntimeError("No bot username specified and I cannot get it from Telegram")

        yield self.bot.setServiceParent(self)
