import xbmc
import kodigui
from lib.util import T
from lib import util
import plexnet


class VideoSettingsDialog(kodigui.BaseDialog, util.CronReceiver):
    xmlFile = 'script-plex-video_settings_dialog.xml'
    path = util.ADDON.getAddonInfo('path')
    theme = 'Main'
    res = '1080i'
    width = 1920
    height = 1080

    SETTINGS_LIST_ID = 100

    def __init__(self, *args, **kwargs):
        kodigui.BaseDialog.__init__(self, *args, **kwargs)
        self.video = kwargs.get('video')
        self.viaOSD = kwargs.get('via_osd')
        self.nonPlayback = kwargs.get('non_playback')

        if not self.video.mediaChoice:
            playerObject = plexnet.plexplayer.PlexPlayer(self.video)
            playerObject.build()

    def onFirstInit(self):
        self.settingsList = kodigui.ManagedControlList(self, self.SETTINGS_LIST_ID, 6)
        self.setProperty('heading', 'Settings')
        if self.viaOSD:
            self.setProperty('via.OSD', '1')
        self.showSettings(True)
        util.CRON.registerReceiver(self)

    def onAction(self, action):
        try:
            if not xbmc.getCondVisibility('Player.HasMedia') and not self.nonPlayback:
                self.doClose()
                return
        except:
            util.ERROR()

        kodigui.BaseDialog.onAction(self, action)

    def onClick(self, controlID):
        if controlID == self.SETTINGS_LIST_ID:
            self.editSetting()

    def onClosed(self):
        util.CRON.cancelReceiver(self)

    def tick(self):
        if self.nonPlayback:
            return

        if not xbmc.getCondVisibility('Player.HasMedia'):
            self.doClose()
            return

    def showSettings(self, init=False):
        video = self.video
        override = video.settings.getPrefOverride('local_quality')
        if override is not None and override < 13:
            current = T((32001, 32002, 32003, 32004, 32005, 32006, 32007, 32008, 32009, 32010, 32011, 32012, 32013, 32014)[13 - override])
        else:
            current = u'{0} {1} ({2})'.format(
                plexnet.util.bitrateToString(video.mediaChoice.media.bitrate.asInt() * 1000),
                video.mediaChoice.media.getVideoResolutionString(),
                video.mediaChoice.media.title or 'Original'
            )

        audio, subtitle = self.getAudioAndSubtitleInfo()

        options = [
            ('audio', 'Audio', audio),
            ('subs', 'Subtitles', subtitle),
            ('quality', 'Quality', u'{0}'.format(current)),
            ('kodi_video', 'Kodi Video Settings', ''),
            ('kodi_audio', 'Kodi Audio Settings', '')
        ]

        items = []
        for o in options:
            item = kodigui.ManagedListItem(o[1], o[2], data_source=o[0])
            items.append(item)
        if init:
            self.settingsList.reset()
            self.settingsList.addItems(items)
        else:
            self.settingsList.replaceItems(items)

        self.setFocusId(self.SETTINGS_LIST_ID)

    def getAudioAndSubtitleInfo(self):
        sas = self.video.selectedAudioStream()
        audio = sas and sas.getTitle() or 'None'

        sss = self.video.selectedSubtitleStream()
        if sss:
            if len(self.video.subtitleStreams) > 1:
                subtitle = u'{0} \u2022 {1} More'.format(sss.getTitle(), len(self.video.subtitleStreams) - 1)
            else:
                subtitle = sss.getTitle()
        else:
            if self.video.subtitleStreams:
                subtitle = u'None \u2022 {0} Available'.format(len(self.video.subtitleStreams))
            else:
                subtitle = u'None'

        return audio, subtitle

    def editSetting(self):
        mli = self.settingsList.getSelectedItem()
        if not mli:
            return

        result = mli.dataSource

        if result == 'audio':
            showAudioDialog(self.video, non_playback=self.nonPlayback)
        elif result == 'subs':
            showSubtitlesDialog(self.video, non_playback=self.nonPlayback)
        elif result == 'quality':
            showQualityDialog(self.video, non_playback=self.nonPlayback)
        elif result == 'kodi_video':
            xbmc.executebuiltin('ActivateWindow(OSDVideoSettings)')
        elif result == 'kodi_audio':
            xbmc.executebuiltin('ActivateWindow(OSDAudioSettings)')

        self.showSettings()


class SelectDialog(kodigui.BaseDialog, util.CronReceiver):
    xmlFile = 'script-plex-settings_select_dialog.xml'
    path = util.ADDON.getAddonInfo('path')
    theme = 'Main'
    res = '1080i'
    width = 1920
    height = 1080

    OPTIONS_LIST_ID = 100

    def __init__(self, *args, **kwargs):
        kodigui.BaseDialog.__init__(self, *args, **kwargs)
        self.heading = kwargs.get('heading')
        self.options = kwargs.get('options')
        self.choice = None
        self.nonPlayback = kwargs.get('non_playback')

    def onFirstInit(self):
        self.optionsList = kodigui.ManagedControlList(self, self.OPTIONS_LIST_ID, 8)
        self.setProperty('heading', self.heading)
        self.showOptions()
        util.CRON.registerReceiver(self)

    def onAction(self, action):
        try:
            if not xbmc.getCondVisibility('Player.HasMedia') and not self.nonPlayback:
                self.doClose()
                return
        except:
            util.ERROR()

        kodigui.BaseDialog.onAction(self, action)

    def onClick(self, controlID):
        if controlID == self.OPTIONS_LIST_ID:
            self.setChoice()

    def onClosed(self):
        util.CRON.cancelReceiver(self)

    def tick(self):
        if self.nonPlayback:
            return

        if not xbmc.getCondVisibility('Player.HasMedia'):
            self.doClose()
            return

    def setChoice(self):
        mli = self.optionsList.getSelectedItem()
        if not mli:
            return

        self.choice = self.options[self.optionsList.getSelectedPosition()][0]
        self.doClose()

    def showOptions(self):
        items = []
        for o in self.options:
            item = kodigui.ManagedListItem(o[1], data_source=o[0])
            items.append(item)

        self.optionsList.reset()
        self.optionsList.addItems(items)

        self.setFocusId(self.OPTIONS_LIST_ID)


def showOptionsDialog(heading, options, non_playback=False):
    w = SelectDialog.open(heading=heading, options=options, non_playback=non_playback)
    choice = w.choice
    del w
    return choice


def showAudioDialog(video, non_playback=False):
    options = [(s, s.getTitle()) for s in video.audioStreams]
    choice = showOptionsDialog('Audio', options, non_playback=non_playback)
    if choice is None:
        return

    video.selectStream(choice)


def showSubtitlesDialog(video, non_playback=False):
    options = [(s, s.getTitle()) for s in video.subtitleStreams]
    options.insert(0, (plexnet.plexstream.NoneStream(), 'None'))
    choice = showOptionsDialog('Subtitle', options, non_playback=non_playback)
    if choice is None:
        return

    video.selectStream(choice)


def showQualityDialog(video, non_playback=False):
    options = [(13 - i, T(l)) for (i, l) in enumerate((32001, 32002, 32003, 32004, 32005, 32006, 32007, 32008, 32009, 32010, 32011, 32012, 32013, 32014))]

    choice = showOptionsDialog('Quality', options, non_playback=non_playback)
    if choice is None:
        return

    video.settings.setPrefOverride('local_quality', choice)
    video.settings.setPrefOverride('remote_quality', choice)
    video.settings.setPrefOverride('online_quality', choice)


def showDialog(video, non_playback=False, via_osd=False):
    w = VideoSettingsDialog.open(video=video, non_playback=non_playback, via_osd=via_osd)
    del w
