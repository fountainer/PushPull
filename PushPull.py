import sublime, sublime_plugin
import os
from os.path import join
from shutil import copy, copytree, rmtree

def get_files_folders(self, path = None):
    file_active = None
    if path is None:
        file_active = self.view.file_name()
        path = os.path.dirname(file_active)
    entries = os.listdir(path)
    files = [file for file in entries if os.path.isfile(join(path, file))]
    folders = list(set(entries) - set(files))
    # can not place it in the global environment, because it run only once?
    settings = sublime.load_settings("PushPull.sublime-settings")
    ignored_extensions = tuple(settings.get("ignored_extensions", ()))
    # must after folders = list(set(entries) - set(files))
    files = [file for file in files if not file.lower().endswith(ignored_extensions)]
    return((files, folders, path, file_active))

def get_folder_cloud():
    settings = sublime.load_settings("PushPull.sublime-settings")
    # check the settings
    folder_cloud = settings.get("folder_cloud", "")
    if not folder_cloud:
        sublime.error_message("Please set the cloud folder first")
        raise Exception("Please set the cloud folder first")
    return(folder_cloud)



class PushFileFolderCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        files, folders, path, file_active = self.get_files_folders()
        entries = [file_active, path] + \
                  [join(path, folder) for folder in folders] + \
                  [join(path, file) for file in files]
        # show in the quick panel
        entries_display = [folder + "/" for folder in folders] + files
        entries_display = ["**" + os.path.basename(file_active) + "**", 
                           "**" + os.path.basename(path) + "/**"] + entries_display

        window = self.view.window()
        folder_cloud = get_folder_cloud()

        def on_done(index):
            # copy file
            if index > (len(folders) + 1):
                copy(entries[index], folder_cloud)
            # copy subdirectory or this directory
            elif index >= 1:
                copytree(entries[index], join(folder_cloud, os.path.basename(entries[index])))
            # copy this file
            elif index == 0:
                copy(entries[index], folder_cloud)
            else:
                pass
        window.show_quick_panel(entries_display, on_done)

    # use method outside class
    get_files_folders = get_files_folders


class PullFileFolderCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        folder_cloud = get_folder_cloud()
        files, folders, path, _ = self.get_files_folders(folder_cloud)
        entries = [join(path, folder) for folder in folders] + \
                  [join(path, file) for file in files]
        # show in the quick panel
        entries_display = [folder + "/" for folder in folders] + files
        folder_current = os.path.dirname(self.view.file_name())

        window = self.view.window()
 
        def on_done(index):
            # copy file
            if index > len(folders) - 1:
                copy(entries[index], folder_current)
                window.open_file(join(folder_current, os.path.basename(entries[index])))
                os.remove(entries[index])
            # copy subdirectory
            elif index >= 0:
                entry_basename = os.path.basename(entries[index])
                folder_dst = join(folder_current, entry_basename)
                is_overwrite = True
                if entry_basename in os.listdir(folder_current):
                    is_overwrite = sublime.ok_cancel_dialog(entry_basename + " Already exist, overwrite it?")
                    if is_overwrite:
                        if os.path.isfile(folder_dst):
                            os.remove(folder_dst)
                        else:
                            rmtree(folder_dst)
                    else:
                        is_overwrite = False
                if is_overwrite:
                    copytree(entries[index], folder_dst)
                    window.active_view().run_command("open_files", {"path": folder_dst})
                    rmtree(entries[index])
            else:
                pass

        window.show_quick_panel(entries_display, on_done)

        # use method outside class
    get_files_folders = get_files_folders