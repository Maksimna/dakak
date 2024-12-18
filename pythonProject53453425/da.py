import sys
# не забыть скачать pip install pyqt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QPushButton, QVBoxLayout, QWidget, QLineEdit, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
import sqlite3


class BookstoreApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Книжный магазин")
        self.setGeometry(100, 100, 800, 500)

        self.conn = sqlite3.connect("bookstore.db")
        self.create_table()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()


        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название книги")
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Автор")
        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("Год книги")

        self.add_button = QPushButton("Добавить книгу")
        self.add_button.clicked.connect(self.add_book)

        self.layout.addWidget(QLabel("Добавить книгу"))
        self.layout.addWidget(self.title_input)
        self.layout.addWidget(self.author_input)
        self.layout.addWidget(self.year_input)
        self.layout.addWidget(self.add_button)


        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по названию или автору")
        self.search_button = QPushButton("Искать")
        self.search_button.clicked.connect(self.search_books)
        self.layout.addWidget(self.search_input)
        self.layout.addWidget(self.search_button)

       
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Автор", "Год книги", "Изменить"])
        self.layout.addWidget(self.table)

        self.refresh_button = QPushButton("Обновить список")
        self.refresh_button.clicked.connect(self.load_books)
        self.layout.addWidget(self.refresh_button)

        self.delete_button = QPushButton("Удалить выбранную книгу")
        self.delete_button.clicked.connect(self.delete_book)
        self.layout.addWidget(self.delete_button)

        self.central_widget.setLayout(self.layout)

        self.load_books()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            year_book INTEGER
        )
        """)
        self.conn.commit()

    def add_book(self):
        title = self.title_input.text()
        author = self.author_input.text()
        year_book = self.year_input.text()

        if not title or not author or not year_book:
            QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены!")
            return

        try:
            year_book = int(year_book)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Год должен быть числом!")
            return

        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO books (title, author, year_book) VALUES (?, ?, ?)",
            (title, author, year_book)
        )
        self.conn.commit()

        QMessageBox.information(self, "Успех", "Книга добавлена!")
        self.load_books()

    def load_books(self, query=None):
        cursor = self.conn.cursor()
        if query:
            cursor.execute(query)
        else:
            cursor.execute("SELECT id, title, author, year_book FROM books")
        books = cursor.fetchall()

        self.table.setRowCount(len(books))
        for row_idx, (book_id, title, author, year_book) in enumerate(books):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(book_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(title))
            self.table.setItem(row_idx, 2, QTableWidgetItem(author))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(year_book)))

            edit_button = QPushButton("Изменить")
            edit_button.clicked.connect(lambda _, book_id=book_id: self.edit_book(book_id))
            self.table.setCellWidget(row_idx, 4, edit_button)

    def delete_book(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите книгу для удаления!")
            return

        reply = QMessageBox.question(
            self, "Подтверждение удаления", "Вы уверены, что хотите удалить эту книгу?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            book_id = self.table.item(selected_row, 0).text()
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            self.conn.commit()

            QMessageBox.information(self, "Успех", "Книга удалена!")
            self.load_books()

    def search_books(self):
        search_term = self.search_input.text()
        if not search_term:
            QMessageBox.warning(self, "Ошибка", "Введите текст для поиска!")
            return

        query = f"SELECT id, title, author, year_book FROM books WHERE title LIKE '%{search_term}%' OR author LIKE '%{search_term}%'"
        self.load_books(query)

    def edit_book(self, book_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT title, author, year_book FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()

        if book:
            title, author, year_book = book

            edit_window = QWidget()
            edit_window.setWindowTitle("Редактировать книгу")
            layout = QVBoxLayout()

            title_input = QLineEdit(title)
            author_input = QLineEdit(author)
            year_input = QLineEdit(str(year_book))

            save_button = QPushButton("Сохранить изменения")
            save_button.clicked.connect(
                lambda: self.save_edited_book(book_id, title_input.text(), author_input.text(), year_input.text(),
                                              edit_window))

            layout.addWidget(QLabel("Название книги"))
            layout.addWidget(title_input)
            layout.addWidget(QLabel("Автор"))
            layout.addWidget(author_input)
            layout.addWidget(QLabel("Год книги"))
            layout.addWidget(year_input)
            layout.addWidget(save_button)

            edit_window.setLayout(layout)
            edit_window.setGeometry(200, 200, 300, 200)
            edit_window.show()

    def save_edited_book(self, book_id, new_title, new_author, new_year, edit_window):
        try:
            new_year = int(new_year)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Год должен быть числом!")
            return

        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE books SET title = ?, author = ?, year_book = ? WHERE id = ?",
            (new_title, new_author, new_year, book_id)
        )
        self.conn.commit()

        QMessageBox.information(self, "Успех", "Книга обновлена!")
        self.load_books()
        edit_window.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookstoreApp()
    window.show()
    sys.exit(app.exec_())
