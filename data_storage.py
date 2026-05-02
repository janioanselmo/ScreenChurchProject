import json
import os
import re
import shutil
import sqlite3

from PyQt5.QtWidgets import QFileDialog, QMessageBox

from constants import (
    IMAGE_EXTENSIONS,
    LAYOUT_PRESETS_FILENAME,
    VIDEO_EXTENSIONS,
)


class DataStorageMixin:
    """Local ScreenChurchData folder, database and library indexing helpers."""

    def base_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

    def default_data_root(self):
        """Return the ScreenChurchData root.

        Portable/source installations can keep a ScreenChurchData folder next to
        screenChurch.py. When that folder exists, it is preferred so users can
        place bibles, songs and backgrounds directly in the project folder. If
        it does not exist, the user Documents folder is used.
        """
        portable_root = os.path.join(self.base_dir(), "ScreenChurchData")
        if os.path.isdir(portable_root):
            return portable_root
        documents = os.path.join(os.path.expanduser("~"), "Documents")
        if not os.path.isdir(documents):
            documents = os.path.expanduser("~")
        return os.path.join(documents, "ScreenChurchData")

    def setup_data_directories(self):
        env_root = os.environ.get("SCREENCHURCH_DATA_DIR")
        portable_root = os.path.join(self.base_dir(), "ScreenChurchData")
        stored_root = self.settings.value("data_root", "")
        if env_root:
            data_root = env_root
        elif os.path.isdir(portable_root):
            data_root = portable_root
        else:
            data_root = stored_root or self.default_data_root()
        self._data_root = os.path.abspath(data_root)
        self.settings.setValue("data_root", self._data_root)
        self._data_subdirs = [
            "config",
            "database",
            "bibles",
            "songs",
            os.path.join("songs", "exports"),
            "themes",
            "services",
            "exports",
            os.path.join("exports", "presets"),
            os.path.join("exports", "songs"),
            os.path.join("exports", "services"),
            "backups",
            "media",
            os.path.join("media", "backgrounds"),
            os.path.join("media", "backgrounds", "images"),
            os.path.join("media", "backgrounds", "videos"),
            os.path.join("media", "images"),
            os.path.join("media", "videos"),
        ]
        for subdir in self._data_subdirs:
            os.makedirs(self.data_path(subdir), exist_ok=True)
        self.init_database()
        self.write_data_readme()

    def data_path(self, *parts):
        return os.path.join(self._data_root, *parts)

    def database_path(self):
        return self.data_path("database", "screenchurch.db")

    def init_database(self):
        with sqlite3.connect(self.database_path()) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS media_library ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "path TEXT NOT NULL UNIQUE, "
                "created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS songs ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "title TEXT NOT NULL UNIQUE, "
                "data_json TEXT NOT NULL, "
                "updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS bibles ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT NOT NULL UNIQUE, "
                "path TEXT NOT NULL, "
                "updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS app_config ("
                "key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            conn.commit()

    def relative_to_data_root(self, path):
        if not path:
            return ""
        path = os.path.abspath(path)
        try:
            rel = os.path.relpath(path, self._data_root)
            if not rel.startswith("..") and not os.path.isabs(rel):
                return rel.replace("\\", "/")
        except ValueError:
            pass
        return path

    def absolute_from_data_root(self, path):
        if not path:
            return ""
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(self._data_root, path))

    def unique_destination(self, folder, filename):
        os.makedirs(folder, exist_ok=True)
        base, ext = os.path.splitext(os.path.basename(filename))
        safe_base = re.sub(r"[^\w\-.]+", "_", base, flags=re.UNICODE).strip("_") or "arquivo"
        candidate = os.path.join(folder, safe_base + ext.lower())
        counter = 2
        while os.path.exists(candidate):
            candidate = os.path.join(folder, f"{safe_base}_{counter}{ext.lower()}")
            counter += 1
        return candidate

    def copy_into_data_folder(self, source_path, relative_folder):
        if not source_path or not os.path.exists(source_path):
            return source_path
        source_path = os.path.abspath(source_path)
        destination_folder = self.data_path(relative_folder)
        try:
            if os.path.commonpath([source_path, self._data_root]) == self._data_root:
                return source_path
        except ValueError:
            pass
        destination = self.unique_destination(destination_folder, source_path)
        shutil.copy2(source_path, destination)
        return destination

    def import_media_file(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            return self.copy_into_data_folder(filepath, os.path.join("media", "images"))
        if ext in VIDEO_EXTENSIONS:
            return self.copy_into_data_folder(filepath, os.path.join("media", "videos"))
        return filepath

    def import_background_file(self, filepath, media_type):
        folder = os.path.join("media", "backgrounds", "videos" if media_type == "video" else "images")
        return self.copy_into_data_folder(filepath, folder)

    def import_bible_file(self, filepath):
        return self.copy_into_data_folder(filepath, "bibles")

    def write_data_readme(self):
        filename = self.data_path("README_ScreenChurchData.txt")
        if os.path.exists(filename):
            return
        content = (
            "ScreenChurchData\n"
            "================\n\n"
            "Esta pasta guarda os dados do ScreenChurch separados do programa.\n"
            "Faça backup desta pasta para preservar músicas, Bíblias, fundos, cultos e configurações.\n\n"
            "Estrutura principal:\n"
            "- bibles/: Bíblias em JSON, incluindo o formato damarals/biblias.\n"
            "- database/screenchurch.db: banco SQLite com músicas, biblioteca de mídias e índice de Bíblias.\n"
            "- media/: imagens e vídeos importados.\n"
            "- media/backgrounds/: fundos de músicas e Bíblia.\n"
            "- themes/: temas em JSON.\n"
            "- services/: cultos salvos.\n"
            "- config/: presets de layout e configurações.\n"
            "\n"
            "Coloque novos arquivos diretamente nas pastas correspondentes e use \"Arquivo > Atualizar biblioteca\".\n"
            "Bíblias JSON: bibles/ no formato damarals/biblias ou ScreenChurch.\n"
            "Letras TXT/JSON: songs/; linha em branco separa slides.\n"
            "Fundos: media/backgrounds/images/ ou media/backgrounds/videos/.\n"
        )
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)

    def open_data_folder(self):
        try:
            if os.name == "nt":
                os.startfile(self._data_root)  # type: ignore[attr-defined]
            else:
                QMessageBox.information(self, "Pasta de dados", self._data_root)
        except OSError as error:
            QMessageBox.warning(self, "Pasta de dados", str(error))

    def backup_data_folder(self):
        default_name = os.path.join(self.data_path("backups"), "screenchurch_backup")
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar backup", default_name, "Arquivo ZIP (*.zip)"
        )
        if not filename:
            return
        if filename.lower().endswith(".zip"):
            filename = filename[:-4]
        try:
            zip_path = shutil.make_archive(filename, "zip", self._data_root)
            self.show_status_message(f"Backup criado: {zip_path}", 6000)
        except OSError as error:
            QMessageBox.warning(self, "Backup", str(error))


    def discover_media_files(self):
        folders = [
            self.data_path("media", "images"),
            self.data_path("media", "videos"),
            self.data_path("media", "backgrounds", "images"),
            self.data_path("media", "backgrounds", "videos"),
        ]
        known = set(self.media_library)
        for folder in folders:
            if not os.path.isdir(folder):
                continue
            for root, _dirs, files in os.walk(folder):
                for name in files:
                    path = os.path.join(root, name)
                    if self.is_supported_file(path) and path not in known:
                        self.media_library.append(path)
                        known.add(path)

    def discover_bible_files(self):
        known_paths = {os.path.abspath(v.get("source_path", "")) for v in self.bible_versions if v.get("source_path")}
        for name in sorted(os.listdir(self.data_path("bibles"))):
            if not name.lower().endswith(".json"):
                continue
            path = os.path.abspath(self.data_path("bibles", name))
            if path in known_paths:
                continue
            version = self.load_bible_from_file(path)
            if version:
                version["source_path"] = path
                existing_names = {v.get("name") for v in self.bible_versions}
                if version.get("name") in existing_names:
                    version["name"] = self.version_name_from_filename(path) or version.get("name")
                self.bible_versions.append(version)
                known_paths.add(path)

    def discover_song_files(self):
        """Import TXT/JSON songs placed in ScreenChurchData/songs.

        This is intentionally conservative: songs already present in the
        database are not overwritten, preserving edits made inside the app.
        To update an existing song, use the import menu or edit it manually.
        """
        songs_folder = self.data_path("songs")
        if not os.path.isdir(songs_folder):
            return
        existing_titles = {song.get("title") for song in self.songs}
        imported_songs = []
        ignored_dirs = {
            os.path.abspath(self.data_path("songs", "exports")),
        }
        for root, dirs, files in os.walk(songs_folder):
            root_abs = os.path.abspath(root)
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) not in ignored_dirs]
            if root_abs in ignored_dirs:
                continue
            for name in sorted(files):
                ext = os.path.splitext(name)[1].lower()
                if ext not in {".txt", ".json"}:
                    continue
                path = os.path.join(root, name)
                try:
                    if ext == ".txt":
                        with open(path, "r", encoding="utf-8") as file:
                            song = self.parse_song_txt(file.read(), default_title=name)
                        candidates = [song] if song else []
                    else:
                        with open(path, "r", encoding="utf-8") as file:
                            data = json.load(file)
                        if isinstance(data, dict) and "songs" in data:
                            candidates = data.get("songs") or []
                        elif isinstance(data, list):
                            candidates = data
                        else:
                            candidates = [data]
                    for candidate in candidates:
                        normalized = self.normalize_song_data(candidate)
                        if not normalized:
                            continue
                        title = normalized.get("title")
                        if not title or title in existing_titles:
                            continue
                        normalized["source_path"] = path
                        imported_songs.append(normalized)
                        existing_titles.add(title)
                except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
                    continue
        if imported_songs:
            self.songs.extend(imported_songs)
            self.songs.sort(key=lambda item: item.get("title", "").lower())

    def reload_local_libraries(self):
        self.load_local_libraries()
        self.refresh_all_lists()
        self.refresh_target_panel_combo()
        self.show_status_message("Biblioteca atualizada.", 4000)

    def load_local_libraries(self):
        self.init_database()
        self.media_library = []
        self.songs = []
        self.bible_versions = []
        with sqlite3.connect(self.database_path()) as conn:
            for (path,) in conn.execute("SELECT path FROM media_library ORDER BY path"):
                absolute = self.absolute_from_data_root(path)
                if os.path.exists(absolute):
                    self.media_library.append(absolute)
            for (data_json,) in conn.execute("SELECT data_json FROM songs ORDER BY title"):
                try:
                    song = json.loads(data_json)
                    self.songs.append(self.resolve_song_paths(song))
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
            bible_rows = list(conn.execute("SELECT name, path FROM bibles ORDER BY name"))

        # Backward compatibility: migrate the old single JSON library if present.
        legacy_path = os.path.join(self.base_dir(), "screenchurch_library.json")
        if os.path.exists(legacy_path) and not (self.media_library or self.songs or bible_rows):
            data = self.load_json_file(legacy_path, default={})
            self.media_library = [p for p in data.get("media_library", []) if os.path.exists(p)]
            self.songs = data.get("songs", [])
            self.bible_versions = []
            for version in data.get("bible_versions", []):
                if not isinstance(version, dict):
                    continue
                name = version.get("name", "Bíblia")
                safe_name = re.sub(r"[^\w\-.]+", "_", name, flags=re.UNICODE).strip("_") or "biblia"
                bible_file = self.data_path("bibles", f"{safe_name}.json")
                try:
                    with open(bible_file, "w", encoding="utf-8") as file:
                        json.dump(version, file, ensure_ascii=False, indent=2)
                    version["source_path"] = bible_file
                except OSError:
                    pass
                self.bible_versions.append(version)
            self.save_local_libraries()
        else:
            for name, path in bible_rows:
                absolute = self.absolute_from_data_root(path)
                version = self.load_bible_from_file(absolute, name)
                if version:
                    version["source_path"] = absolute
                    self.bible_versions.append(version)

        self.discover_media_files()
        self.discover_bible_files()
        self.discover_song_files()
        self.save_local_libraries()
        self.refresh_bible_versions()

    def load_bible_from_file(self, filename, fallback_name=None):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
            version = self.normalize_bible_version(data, filename)
            if version and fallback_name:
                version["name"] = self.readable_bible_version_name(fallback_name)
            return version
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return None

    def resolve_descriptor_paths(self, descriptor):
        if not isinstance(descriptor, dict):
            return descriptor
        descriptor = dict(descriptor)
        if descriptor.get("path"):
            descriptor["path"] = self.absolute_from_data_root(descriptor.get("path"))
        options = dict(descriptor.get("options", {}) or {})
        if options.get("background_path"):
            options["background_path"] = self.absolute_from_data_root(options.get("background_path"))
            descriptor["options"] = options
        return descriptor

    def relativize_descriptor_paths(self, descriptor):
        if not isinstance(descriptor, dict):
            return descriptor
        descriptor = dict(descriptor)
        if descriptor.get("path"):
            descriptor["path"] = self.relative_to_data_root(descriptor.get("path"))
        options = dict(descriptor.get("options", {}) or {})
        if options.get("background_path"):
            options["background_path"] = self.relative_to_data_root(options.get("background_path"))
            descriptor["options"] = options
        return descriptor

    def resolve_song_paths(self, song):
        song = dict(song or {})
        background = song.get("default_background")
        if isinstance(background, dict) and background.get("path"):
            background = dict(background)
            background["path"] = self.absolute_from_data_root(background.get("path"))
            song["default_background"] = background
        sections = []
        for section in song.get("sections", []) or []:
            section = dict(section)
            bg = section.get("background")
            if isinstance(bg, dict) and bg.get("path"):
                bg = dict(bg)
                bg["path"] = self.absolute_from_data_root(bg.get("path"))
                section["background"] = bg
            sections.append(section)
        song["sections"] = sections
        return song

    def relativize_song_paths(self, song):
        song = dict(song or {})
        background = song.get("default_background")
        if isinstance(background, dict) and background.get("path"):
            background = dict(background)
            background["path"] = self.relative_to_data_root(background.get("path"))
            song["default_background"] = background
        sections = []
        for section in song.get("sections", []) or []:
            section = dict(section)
            bg = section.get("background")
            if isinstance(bg, dict) and bg.get("path"):
                bg = dict(bg)
                bg["path"] = self.relative_to_data_root(bg.get("path"))
                section["background"] = bg
            sections.append(section)
        song["sections"] = sections
        return song

    def save_local_libraries(self):
        self.init_database()
        with sqlite3.connect(self.database_path()) as conn:
            conn.execute("DELETE FROM media_library")
            for path in self.media_library:
                conn.execute(
                    "INSERT OR IGNORE INTO media_library(path) VALUES (?)",
                    (self.relative_to_data_root(path),),
                )
            conn.execute("DELETE FROM songs")
            for song in self.songs:
                stored_song = self.relativize_song_paths(song)
                conn.execute(
                    "INSERT OR REPLACE INTO songs(title, data_json, updated_at) "
                    "VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (stored_song.get("title", "Sem título"), json.dumps(stored_song, ensure_ascii=False)),
                )
            conn.execute("DELETE FROM bibles")
            for version in self.bible_versions:
                source_path = version.get("source_path", "")
                if source_path:
                    conn.execute(
                        "INSERT OR REPLACE INTO bibles(name, path, updated_at) "
                        "VALUES (?, ?, CURRENT_TIMESTAMP)",
                        (version.get("name", "Bíblia"), self.relative_to_data_root(source_path)),
                    )
            conn.commit()

    def refresh_all_lists(self):
        self.refresh_media_list()
        self.refresh_song_list()
        self.refresh_bible_versions()
        self.refresh_service_list()

    @staticmethod
    def load_json_file(filename, default=None):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            return default if default is not None else {}

    @staticmethod
    def save_json_file(filename, data):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
