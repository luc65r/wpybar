import gi
import i3ipc
from mpd import MPDClient
import sys
import time
import threading

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gio, GLib, GObject, Gtk, GtkLayerShell
from gi.repository import AppIndicator3 as AppIndicator


class MusicLabel(Gtk.Label):
    def __init__(self):
        Gtk.Label.__init__(self)

        self.mpd = MPDClient()
        self.mpd.connect("localhost", 6600)
        self.update()

        GObject.signal_new("mpd_player", self, GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_PYOBJECT, ())
        self.connect("mpd_player", self.update)

        def thread_work():
            while True:
                self.mpd.idle("player")
                self.emit("mpd_player")

        self.t = threading.Thread(target=thread_work)
        self.t.daemon = True
        self.t.start()

    def update(self, *args):
        song = self.mpd.currentsong()
        if song:
            self.set_label(f"{song['artist']} - {song['title']}")
        else:
            self.set_label("")


class ClockLabel(Gtk.Label):
    def __init__(self):
        Gtk.Label.__init__(self)
        self.update()
        GLib.timeout_add_seconds(1, self.update)

    def update(self):
        self.set_label(time.strftime("%X"))
        return True


class WorkspaceButton(Gtk.Button):
    def __init__(self, connection, ipc_data):
        Gtk.Button.__init__(self)

        self.sway = connection
        self.uid = ipc_data['id']
        self.num = ipc_data['num']
        self.name = ipc_data['name']
        self.focused = ipc_data['focused']

        self.set_label(self.name)

    def do_clicked(self):
        self.sway.command(f"workspace number {self.num}")


class SwayWorkspaces(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)

        self.sway = i3ipc.Connection()

        ws = self.sway.get_workspaces()
        for w in ws:
            wb = WorkspaceButton(self.sway, w.ipc_data)
            self.pack_start(wb, False, False, 0)
            wb.show()

        self.sway.on(i3ipc.Event.WORKSPACE_FOCUS, self.on_focus)
        self.sway.on(i3ipc.Event.WORKSPACE_EMPTY, self.on_empty)
        self.sway.on(i3ipc.Event.WORKSPACE_INIT, self.on_init)

        self.t = threading.Thread(target=self.sway.main)
        self.t.daemon = True
        self.t.start()

    def get_workspace(self, uid):
        ws = self.get_children()
        for w in ws:
            if w.uid == uid:
                return w

    def on_focus(self, _, e):
        current = self.get_workspace(e.current.id)
        old = self.get_workspace(e.old.id)
        old.focused = False
        current.focused = True

    def on_empty(self, _, e):
        w = self.get_workspace(e.current.id)
        w.destroy()

    def on_init(self, _, e):
        wb = WorkspaceButton(self.sway, e.current.ipc_data)
        self.pack_start(wb, False, False, 0)

        i = 0
        ws = self.get_children()
        for w in ws:
            if w.num > wb.num:
                break
            i += 1

        self.reorder_child(wb, i)
        wb.show()


class Bar(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.auto_exclusive_zone_enable(self)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 0)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.BOTTOM, 0)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)

        self.left = [SwayWorkspaces()]
        self.center = MusicLabel()
        self.right = [ClockLabel()]

        self.box = Gtk.Box()
        self.box.set_homogeneous(False)

        for w in self.left:
            self.box.pack_start(w, False, False, 0)
            w.show()

        self.box.set_center_widget(self.center)
        self.center.show()

        for w in self.right:
            self.box.pack_end(w, False, False, 0)
            w.show()

        self.add(self.box)
        self.box.show()


class App(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="com.github.luc65r.wpybar",
            **kwargs,
        )
        self.win = None

    def do_activate(self):
        if not self.win:
            self.win = Bar(application=self)

        self.win.present()


if __name__ == "__main__":
    app = App()
    app.run(sys.argv)
