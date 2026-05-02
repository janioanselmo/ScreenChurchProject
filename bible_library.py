import json
import os

from PyQt5.QtWidgets import QFileDialog, QListWidgetItem, QMessageBox


class BibleLibraryMixin:
    """Bible import, normalization, search and projection helpers."""

    def import_bible_json(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Importar Bíblia JSON", "", "JSON (*.json)")
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
            version = self.normalize_bible_version(data, filename)
            if not version:
                QMessageBox.warning(self, "Formato inválido", "Não foi possível reconhecer esta Bíblia JSON.")
                return
            copied_file = self.import_bible_file(filename)
            version["source_path"] = copied_file
            self.bible_versions = [v for v in self.bible_versions if v.get("name") != version.get("name")]
            self.bible_versions.append(version)
            self.save_local_libraries()
            self.refresh_bible_versions()
            self.show_status_message(f"Bíblia importada: {version.get('name')}", 5000)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            QMessageBox.warning(self, "Erro ao importar Bíblia", str(error))

    def normalize_bible_version(self, data, filename=None):
        """Normalize supported Bible JSON formats to ScreenChurch format."""
        if isinstance(data, list):
            return self.normalize_damarals_bible(data, filename)

        if not isinstance(data, dict):
            return None

        # ScreenChurch native/recommended format.
        name = (
            data.get("version")
            or data.get("name")
            or data.get("translation")
            or self.version_name_from_filename(filename)
            or "Bíblia importada"
        )
        books = data.get("books", [])
        if not isinstance(books, list):
            return None

        normalized_books = []
        for book in books:
            book_name = book.get("name") or book.get("book")
            chapters = book.get("chapters", [])
            if not book_name or not isinstance(chapters, list):
                continue

            normalized_chapters = []
            for chapter_index, chapter in enumerate(chapters, start=1):
                if isinstance(chapter, dict):
                    number = int(chapter.get("number", chapter.get("chapter", chapter_index)))
                    verses = chapter.get("verses", [])
                elif isinstance(chapter, list):
                    number = chapter_index
                    verses = chapter
                else:
                    continue

                normalized_verses = self.normalize_verse_list(verses)
                normalized_chapters.append({"number": number, "verses": normalized_verses})

            normalized_books.append({"name": book_name, "chapters": normalized_chapters})

        return {"name": name, "books": normalized_books} if normalized_books else None

    def normalize_damarals_bible(self, data, filename=None):
        """Normalize damarals/biblias JSON format.

        Expected source shape:
        [
            {
                "abbrev": "Gn",
                "chapters": [
                    ["Verse 1 text", "Verse 2 text"],
                    ...
                ]
            },
            ...
        ]
        """
        normalized_books = []
        for book in data:
            if not isinstance(book, dict):
                continue

            abbrev = str(book.get("abbrev", "")).strip()
            book_name = book.get("name") or book.get("book")
            book_name = book_name or self.bible_book_name_from_abbrev(abbrev)
            chapters = book.get("chapters", [])

            if not book_name or not isinstance(chapters, list):
                continue

            normalized_chapters = []
            for chapter_index, verses in enumerate(chapters, start=1):
                normalized_chapters.append(
                    {
                        "number": chapter_index,
                        "verses": self.normalize_verse_list(verses),
                    }
                )

            normalized_books.append(
                {
                    "name": book_name,
                    "abbrev": abbrev,
                    "chapters": normalized_chapters,
                }
            )

        version_name = self.version_name_from_filename(filename) or "Bíblia damarals"
        return {"name": version_name, "books": normalized_books} if normalized_books else None

    def normalize_verse_list(self, verses):
        """Normalize a list of verse strings or verse dictionaries."""
        normalized_verses = []
        if not isinstance(verses, list):
            return normalized_verses

        for verse_index, verse in enumerate(verses, start=1):
            if isinstance(verse, dict):
                number = int(verse.get("number", verse.get("verse", verse_index)))
                text = str(verse.get("text", ""))
            else:
                number = verse_index
                text = str(verse)

            normalized_verses.append({"number": number, "text": text})

        return normalized_verses

    def version_name_from_filename(self, filename):
        """Return a readable Bible version name from a JSON filename."""
        if not filename:
            return ""

        base_name = os.path.splitext(os.path.basename(filename))[0].strip()
        return base_name.capitalize() if base_name else ""

    def bible_book_name_from_abbrev(self, abbrev):
        """Convert common Portuguese Bible abbreviations to book names."""
        mapping = {
            "gn": "Gênesis",
            "ex": "Êxodo",
            "lv": "Levítico",
            "nm": "Números",
            "dt": "Deuteronômio",
            "js": "Josué",
            "jz": "Juízes",
            "rt": "Rute",
            "1sm": "1 Samuel",
            "2sm": "2 Samuel",
            "1rs": "1 Reis",
            "2rs": "2 Reis",
            "1cr": "1 Crônicas",
            "2cr": "2 Crônicas",
            "ed": "Esdras",
            "ne": "Neemias",
            "et": "Ester",
            "jó": "Jó",
            "jo": "Jó",
            "sl": "Salmos",
            "pv": "Provérbios",
            "ec": "Eclesiastes",
            "ct": "Cânticos",
            "is": "Isaías",
            "jr": "Jeremias",
            "lm": "Lamentações",
            "ez": "Ezequiel",
            "dn": "Daniel",
            "os": "Oseias",
            "jl": "Joel",
            "am": "Amós",
            "ob": "Obadias",
            "jn": "Jonas",
            "mq": "Miqueias",
            "na": "Naum",
            "hc": "Habacuque",
            "sf": "Sofonias",
            "ag": "Ageu",
            "zc": "Zacarias",
            "ml": "Malaquias",
            "mt": "Mateus",
            "mc": "Marcos",
            "lc": "Lucas",
            "joa": "João",
            "joão": "João",
            "at": "Atos",
            "rm": "Romanos",
            "1co": "1 Coríntios",
            "2co": "2 Coríntios",
            "gl": "Gálatas",
            "ef": "Efésios",
            "fp": "Filipenses",
            "cl": "Colossenses",
            "1ts": "1 Tessalonicenses",
            "2ts": "2 Tessalonicenses",
            "1tm": "1 Timóteo",
            "2tm": "2 Timóteo",
            "tt": "Tito",
            "fm": "Filemom",
            "hb": "Hebreus",
            "tg": "Tiago",
            "1pe": "1 Pedro",
            "2pe": "2 Pedro",
            "1jo": "1 João",
            "2jo": "2 João",
            "3jo": "3 João",
            "jd": "Judas",
            "ap": "Apocalipse",
        }
        key = str(abbrev).strip().lower()
        return mapping.get(key, abbrev)

    def refresh_bible_versions(self):
        if hasattr(self, "bible_version_combo"):
            self.bible_version_combo.clear()
            for version in self.bible_versions:
                self.bible_version_combo.addItem(version.get("name", "Bíblia"), version.get("name"))
        if self.bible_dialog:
            self.bible_dialog.refresh_versions()

    def current_bible_version(self):
        name = self.bible_version_combo.currentData()
        for version in self.bible_versions:
            if version.get("name") == name:
                return version
        return self.bible_versions[0] if self.bible_versions else None

    def search_bible_reference(self):
        version = self.current_bible_version()
        if not version:
            QMessageBox.information(self, "Bíblia", "Importe uma Bíblia JSON primeiro.")
            return
        book_name = self.bible_book_edit.text().strip().lower()
        try:
            chapter_number = int(self.bible_chapter_edit.text())
            start = int(self.bible_start_edit.text())
            end = int(self.bible_end_edit.text() or start)
        except ValueError:
            QMessageBox.warning(self, "Referência inválida", "Informe capítulo e versículos numéricos.")
            return
        book = next((b for b in version.get("books", []) if b.get("name", "").lower().startswith(book_name)), None)
        if not book:
            QMessageBox.warning(self, "Livro não encontrado", "Livro não encontrado na versão selecionada.")
            return
        chapter = next((c for c in book.get("chapters", []) if c.get("number") == chapter_number), None)
        if not chapter:
            QMessageBox.warning(self, "Capítulo não encontrado", "Capítulo não encontrado.")
            return
        selected = [v for v in chapter.get("verses", []) if start <= int(v.get("number", 0)) <= end]
        reference = f"{book.get('name')} {chapter_number}:{start}" + (f"-{end}" if end != start else "")
        body = "\n".join(f"{v.get('number')}. {v.get('text')}" for v in selected)
        self.bible_result_title = reference
        self.bible_result_text.setPlainText(body)

    def search_bible_word(self):
        version = self.current_bible_version()
        term = self.bible_search_edit.text().strip().lower()
        if not version or not term:
            return
        results = []
        for book in version.get("books", []):
            for chapter in book.get("chapters", []):
                for verse in chapter.get("verses", []):
                    text = verse.get("text", "")
                    if term in text.lower():
                        results.append(f"{book.get('name')} {chapter.get('number')}:{verse.get('number')} — {text}")
                        if len(results) >= 50:
                            break
        self.bible_result_title = f"Busca: {term}"
        self.bible_result_text.setPlainText("\n\n".join(results) or "Nenhum resultado encontrado.")

    def bible_result_descriptor(self):
        return {
            "type": "text",
            "kind": "bíblia",
            "title": self.bible_result_title or "Bíblia",
            "body": self.bible_result_text.toPlainText().strip(),
            "footer": self.bible_version_combo.currentText(),
            "options": {"text_case": self.bible_text_case, "background_type": "none", "background_path": ""},
        }

    def send_bible_result_to_preview(self):
        descriptor = self.bible_result_descriptor()
        if descriptor["body"]:
            panel_index = self.target_panel_index()
            self.load_descriptor_to_preview(descriptor, panel_index)

    def send_bible_result_to_live(self):
        self.send_bible_result_to_preview()
        self.send_panel_to_live(self.target_panel_index())

    def add_bible_result_to_service(self):
        descriptor = self.bible_result_descriptor()
        if descriptor["body"]:
            self.service_items.append({"label": descriptor["title"], "descriptor": descriptor})
            self.refresh_service_list()

    # ------------------------------------------------------------------
    # Service plan
    # ------------------------------------------------------------------
