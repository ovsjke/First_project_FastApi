import tkinter as tk
from tkinter import messagebox
import requests

BASE_URL = "http://localhost:8000"

token = None
user_role = None


def add_placeholder(entry, text):
    entry.insert(0, text)
    entry.config(fg="gray")

    def on_focus_in(event):
        if entry.get() == text:
            entry.delete(0, tk.END)
            entry.config(fg="black")

    def on_focus_out(event):
        if entry.get() == "":
            entry.insert(0, text)
            entry.config(fg="gray")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("LMS System")
        self.geometry("620x560")
        self.resizable(False, False)
        self.configure(bg="white")
        self.current_frame = None
        self.switch_frame(LoginFrame)



    def switch_frame(self, frame_class):
        if callable(frame_class):
            new_frame = frame_class(self)
        else:
            new_frame = frame_class(self)

        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = new_frame
        self.current_frame.pack(fill="both", expand=True)


class LoginFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        tk.Label(self, text="Вход", font=("Arial", 20)).pack(pady=25)

        self.login = tk.Entry(self, width=35)
        self.login.pack(pady=8)
        add_placeholder(self.login, "Введите логин")

        self.password = tk.Entry(self, width=35, show="*")
        self.password.pack(pady=8)
        add_placeholder(self.password, "Введите пароль")

        tk.Button(self, text="Войти", width=22, command=self.do_login).pack(pady=20)

    def do_login(self):
        global token, user_role

        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": self.login.get(),
                "password": self.password.get(),
            },
        )

        if response.status_code != 200:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
            return

        data = response.json()
        token = data["access_token"]
        user_role = data["role"]

        self.master.switch_frame(MainFrame)


class MainFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", pady=10)

        tk.Label(
            top_bar,
            text=f"Вы вошли как: {user_role}",
            font=("Arial", 12)
        ).pack(side="left", padx=10)

        tk.Button(
            top_bar,
            text="Выйти",
            fg="red",
            command=self.logout
        ).pack(side="right", padx=10)

        tk.Label(self, text="Меню", font=("Arial", 18)).pack(pady=15)

        # ================= ADMIN =================
        if user_role == "admin":
            tk.Button(
                self,
                text="Создать пользователя",
                width=30,
                command=lambda: master.switch_frame(AddUserFrame)
            ).pack(pady=6)

            tk.Button(
                self,
                text="Создать группу",
                width=30,
                command=lambda: master.switch_frame(AddGroupFrame)
            ).pack(pady=6)

            tk.Button(
                self,
                text="Удалить пользователя",
                width=30,
                command=lambda: master.switch_frame(DeleteUserFrame)
            ).pack(pady=6)

            tk.Button(
                self,
                text="Удалить группу",
                width=30,
                command=lambda: master.switch_frame(DeleteGroupFrame)
            ).pack(pady=6)

        # ================= TEACHER =================
        elif user_role == "teacher":
            tk.Button(
                self,
                text="Мои тесты (результаты)",
                width=30,
                command=self.get_teacher_tests
            ).pack(pady=6)

            tk.Button(
                self,
                text="Изменить тест",
                width=30,
                command=self.get_teacher_tests_for_edit
            ).pack(pady=6)

            tk.Button(
                self,
                text="Создать тест",
                width=30,
                command=lambda: master.switch_frame(AddTestFrame)
            ).pack(pady=6)

            tk.Button(
                self,
                text="Добавить вопрос",
                width=30,
                command=lambda: master.switch_frame(AddQuestionFrame)
            ).pack(pady=6)

            tk.Button(
                self,
                text="Удалить тест",
                width=30,
                command=lambda: master.switch_frame(DeleteTestFrame)
            ).pack(pady=6)

            tk.Button(
                self,
                text="Удалить вопрос",
                width=30,
                command=lambda: master.switch_frame(DeleteQuestionFrame)
            ).pack(pady=6)

        # ================= STUDENT =================
        elif user_role == "student":
            tk.Button(
                self,
                text="Посмотреть тесты",
                width=30,
                command=self.get_tests
            ).pack(pady=6)

            tk.Button(
                self,
                text="Мои результаты",
                width=30,
                command=self.get_student_results
            ).pack(pady=6)

    # ================= COMMON =================
    def logout(self):
        global token, user_role
        token = None
        user_role = None
        self.master.switch_frame(LoginFrame)

    # ================= STUDENT =================
    def get_tests(self):
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/student/test", headers=headers)

        if res.status_code != 200:
            messagebox.showerror("Ошибка", res.text)
            return

        data = res.json()
        self.master.switch_frame(lambda m: TestListFrame(m, data))

    def get_student_results(self):
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/student/result", headers=headers)

        if res.status_code != 200:
            messagebox.showerror("Ошибка", res.text)
            return

        data = res.json()
        self.master.switch_frame(lambda m: StudentResultsFrame(m, data))

    # ================= TEACHER =================
    def get_teacher_tests(self):
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/teacher/result", headers=headers)

        if res.status_code != 200:
            messagebox.showerror("Ошибка", res.text)
            return

        data = res.json()
        self.master.switch_frame(lambda m: TeacherTestListFrame(m, data))

    def get_teacher_tests_for_edit(self):
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/teacher/result", headers=headers)

        if res.status_code != 200:
            messagebox.showerror("Ошибка", res.text)
            return

        data = res.json()
        self.master.switch_frame(lambda m: TeacherEditTestListFrame(m, data))
class TestListFrame(tk.Frame):
    def __init__(self, master, tests):
        super().__init__(master)

        tk.Label(self, text="Доступные тесты", font=("Arial", 18)).pack(pady=15)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        if not tests:
            tk.Label(container, text="Нет доступных тестов", font=("Arial", 12)).pack(pady=10)
        else:
            for test in tests:
                row = tk.Frame(container)
                row.pack(fill="x", pady=6)

                tk.Label(
                    row,
                    text=f"{test['title']} (ID: {test['id']})",
                    font=("Arial", 12)
                ).pack(side="left", anchor="w")

                tk.Button(
                    row,
                    text="Начать тест",
                    command=lambda test_id=test["id"]: master.switch_frame(
                        lambda m: OpenTestFrame(m, test_id)
                    )
                ).pack(side="right")

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack(pady=15)


class OpenTestFrame(tk.Frame):
    def __init__(self, master, test_id):
        super().__init__(master)

        self.test_id = test_id
        self.answer_entries = {}

        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/student/test/{test_id}", headers=headers)

        if res.status_code != 200:
            tk.Label(self, text="Ошибка загрузки теста", fg="red", font=("Arial", 14)).pack(pady=20)
            tk.Label(self, text=res.text, wraplength=520).pack(pady=10)

            tk.Button(
                self,
                text="Назад",
                command=lambda: master.switch_frame(lambda m: TestListFrame(m, self.load_tests()))
            ).pack(pady=10)
            return

        data = res.json()

        tk.Label(self, text=data["title"], font=("Arial", 18)).pack(pady=15)

        questions_container = tk.Frame(self)
        questions_container.pack(fill="both", expand=True, padx=20, pady=10)

        for question in data["questions"]:
            q_frame = tk.Frame(questions_container)
            q_frame.pack(fill="x", pady=8)

            tk.Label(
                q_frame,
                text=f"[{question['id']}] {question['description']}",
                wraplength=540,
                justify="left",
                anchor="w",
                font=("Arial", 11)
            ).pack(fill="x")

            entry = tk.Entry(q_frame, width=60)
            entry.pack(fill="x", pady=4)
            add_placeholder(entry, "Введите ответ")

            self.answer_entries[question["id"]] = entry

        tk.Button(
            self,
            text="Отправить результат",
            command=self.submit_test
        ).pack(pady=8)

    def load_tests(self):
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/student/test", headers=headers)
        if res.status_code == 200:
            return res.json()
        return []

    def submit_test(self):
        if not messagebox.askyesno("Подтверждение", "Отправить результат теста?"):
            return

        headers = {"Authorization": f"Bearer {token}"}

        answers = {}
        for question_id, entry in self.answer_entries.items():
            value = entry.get()
            if value == "Введите ответ":
                value = ""
            answers[str(question_id)] = value

        res = requests.post(
            f"{BASE_URL}/student/submit_test/{self.test_id}",
            json={"answer": answers},
            headers=headers,
        )

        if res.status_code != 200:
            messagebox.showerror("Ошибка", res.text)
            return

        data = res.json()
        score = data.get("score", "неизвестно")
        messagebox.showinfo("Успех", f"Тест отправлен.\nВаш результат: {score}")

        self.master.switch_frame(MainFrame)


class AddUserFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        tk.Label(self, text="Создание пользователя", font=("Arial", 16)).pack(pady=15)

        self.login = tk.Entry(self, width=40)
        self.login.pack(pady=6)
        add_placeholder(self.login, "Логин")

        self.password = tk.Entry(self, width=40)
        self.password.pack(pady=6)
        add_placeholder(self.password, "Пароль")

        self.role = tk.Entry(self, width=40)
        self.role.pack(pady=6)
        add_placeholder(self.role, "admin / teacher / student")

        self.group_id = tk.Entry(self, width=40)
        self.group_id.pack(pady=6)
        add_placeholder(self.group_id, "ID группы (только для student)")

        tk.Button(self, text="Создать", command=self.send).pack(pady=12)

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack()

    def send(self):
        headers = {"Authorization": f"Bearer {token}"}

        role = self.role.get().strip()
        group_raw = self.group_id.get().strip()

        group_id = None

        # если студент — группа обязательна
        if role == "student":
            if not group_raw or group_raw == "ID группы (только для student)":
                messagebox.showerror("Ошибка", "Для студента нужно указать группу")
                return
            try:
                group_id = int(group_raw)
            except ValueError:
                messagebox.showerror("Ошибка", "ID группы должен быть числом")
                return

        # для teacher/admin — group_id = None

        res = requests.post(
            f"{BASE_URL}/admin/add_user",
            json={
                "login": self.login.get(),
                "password": self.password.get(),
                "role": role,
                "group_id": group_id,
            },
            headers=headers,
        )

        if res.status_code != 200:
            messagebox.showerror("Ошибка", res.text)
            return



class TeacherEditTestListFrame(tk.Frame):
    def __init__(self, master, tests):
        super().__init__(master)

        tk.Label(self, text="Выберите тест для изменения", font=("Arial", 18)).pack(pady=15)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        if not tests:
            tk.Label(container, text="Нет тестов", font=("Arial", 12)).pack(pady=10)
        else:
            for test in tests:
                row = tk.Frame(container)
                row.pack(fill="x", pady=6)

                tk.Label(
                    row,
                    text=f"{test['title']} (ID: {test['id']}) | попыток: {test['attempt']}",
                    font=("Arial", 12)
                ).pack(side="left", anchor="w")

                tk.Button(
                    row,
                    text="Изменить",
                    command=lambda t=test: master.switch_frame(
                        lambda m: EditTestFrame(m, t)
                    )
                ).pack(side="right")

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack(pady=15)


class EditTestFrame(tk.Frame):
    def __init__(self, master, test_data):
        super().__init__(master)

        self.test_id = test_data["id"]

        tk.Label(self, text=f"Изменение теста ID={self.test_id}", font=("Arial", 16)).pack(pady=15)

        self.title_entry = tk.Entry(self, width=40)
        self.title_entry.pack(pady=6)
        self.title_entry.insert(0, test_data["title"])

        self.attempt_entry = tk.Entry(self, width=40)
        self.attempt_entry.pack(pady=6)
        self.attempt_entry.insert(0, str(test_data["attempt"]))

        tk.Button(
            self,
            text="Сохранить изменения",
            command=self.save_changes
        ).pack(pady=12)

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack()

    def save_changes(self):
        headers = {"Authorization": f"Bearer {token}"}

        title = self.title_entry.get().strip()
        attempt_raw = self.attempt_entry.get().strip()

        if not title:
            messagebox.showerror("Ошибка", "Название теста не может быть пустым")
            return

        try:
            max_attempt = int(attempt_raw)
        except ValueError:
            messagebox.showerror("Ошибка", "Количество попыток должно быть числом")
            return

        res = requests.put(
            f"{BASE_URL}/teacher/edit_test/{self.test_id}",
            json={
                "title": title,
                "max_attemp": max_attempt
            },
            headers=headers,
        )

        if res.status_code != 200:
            messagebox.showerror("Ошибка", res.text)
            return

        messagebox.showinfo("Успех", "Тест успешно изменён")
        self.master.switch_frame(MainFrame)
class AddGroupFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        tk.Label(self, text="Создание группы", font=("Arial", 16)).pack(pady=15)

        self.name = tk.Entry(self, width=40)
        self.name.pack(pady=6)
        add_placeholder(self.name, "Название группы")

        self.teacher = tk.Entry(self, width=40)
        self.teacher.pack(pady=6)
        add_placeholder(self.teacher, "ID преподавателя")

        tk.Button(self, text="Создать", command=self.send).pack(pady=12)

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack()

    def send(self):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            teacher_id = int(self.teacher.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Teacher ID должен быть числом")
            return

        res = requests.post(
            f"{BASE_URL}/admin/add_group",
            json={
                "name": self.name.get(),
                "teacher_id": teacher_id,
            },
            headers=headers,
        )
        messagebox.showinfo("Ответ", res.text)


class DeleteUserFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        tk.Label(self, text="Удаление пользователя", font=("Arial", 16)).pack(pady=15)

        self.user_id = tk.Entry(self, width=40)
        self.user_id.pack(pady=6)
        add_placeholder(self.user_id, "ID пользователя")

        tk.Button(self, text="Удалить", command=self.delete_user).pack(pady=12)

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack()

    def delete_user(self):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            user_id = int(self.user_id.get())
        except ValueError:
            messagebox.showerror("Ошибка", "ID пользователя должен быть числом")
            return

        res = requests.delete(
            f"{BASE_URL}/admin/delete_user/{user_id}",
            headers=headers,
        )
        messagebox.showinfo("Ответ", res.text)


class DeleteGroupFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        tk.Label(self, text="Удаление группы", font=("Arial", 16)).pack(pady=15)

        self.group_id = tk.Entry(self, width=40)
        self.group_id.pack(pady=6)
        add_placeholder(self.group_id, "ID группы")

        tk.Button(self, text="Удалить", command=self.delete_group).pack(pady=12)

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack()

    def delete_group(self):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            group_id = int(self.group_id.get())
        except ValueError:
            messagebox.showerror("Ошибка", "ID группы должен быть числом")
            return

        res = requests.delete(
            f"{BASE_URL}/admin/delete_group/{group_id}",
            headers=headers,
        )
        messagebox.showinfo("Ответ", res.text)


class AddTestFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        tk.Label(self, text="Создание теста", font=("Arial", 16)).pack(pady=15)

        self.title = tk.Entry(self, width=40)
        self.title.pack(pady=6)
        add_placeholder(self.title, "Название теста")

        self.max_attempt = tk.Entry(self, width=40)
        self.max_attempt.pack(pady=6)
        add_placeholder(self.max_attempt, "Максимум попыток (по умолчанию 1)")

        tk.Button(self, text="Создать", command=self.send).pack(pady=12)

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack()

    def send(self):
        headers = {"Authorization": f"Bearer {token}"}

        max_value = self.max_attempt.get().strip()
        if max_value == "" or max_value == "Максимум попыток (по умолчанию 1)":
            max_attempt = 1
        else:
            try:
                max_attempt = int(max_value)
            except ValueError:
                messagebox.showerror("Ошибка", "Максимум попыток должен быть числом")
                return

        res = requests.post(
            f"{BASE_URL}/teacher/add_test",
            json={
                "title": self.title.get(),
                "max_attemp": max_attempt
            },
            headers=headers,
        )
        messagebox.showinfo("Ответ", res.text)


class AddQuestionFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        tk.Label(self, text="Добавление вопроса", font=("Arial", 16)).pack(pady=15)

        self.test_id = tk.Entry(self, width=40)
        self.test_id.pack(pady=6)
        add_placeholder(self.test_id, "ID теста")

        self.desc = tk.Entry(self, width=40)
        self.desc.pack(pady=6)
        add_placeholder(self.desc, "Описание вопроса")

        self.point = tk.Entry(self, width=40)
        self.point.pack(pady=6)
        add_placeholder(self.point, "Баллы (0-1)")

        self.answer = tk.Entry(self, width=40)
        self.answer.pack(pady=6)
        add_placeholder(self.answer, "Правильный ответ")

        tk.Button(self, text="Добавить", command=self.send).pack(pady=12)

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack()

    def send(self):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            test_id = int(self.test_id.get())
            point = float(self.point.get())
        except ValueError:
            messagebox.showerror("Ошибка", "ID теста и баллы должны быть числами")
            return

        res = requests.post(
            f"{BASE_URL}/teacher/add_question",
            json={
                "test_id": test_id,
                "description": self.desc.get(),
                "point": point,
                "answer": self.answer.get(),
            },
            headers=headers,
        )
        messagebox.showinfo("Ответ", res.text)


class DeleteTestFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        tk.Label(self, text="Удаление теста", font=("Arial", 16)).pack(pady=15)

        self.test_id = tk.Entry(self, width=40)
        self.test_id.pack(pady=6)
        add_placeholder(self.test_id, "ID теста")

        tk.Button(self, text="Удалить", command=self.delete_test).pack(pady=12)

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack()

    def delete_test(self):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            test_id = int(self.test_id.get())
        except ValueError:
            messagebox.showerror("Ошибка", "ID теста должен быть числом")
            return

        res = requests.delete(
            f"{BASE_URL}/teacher/delete_test/{test_id}",
            headers=headers,
        )
        messagebox.showinfo("Ответ", res.text)


class DeleteQuestionFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        tk.Label(self, text="Удаление вопроса", font=("Arial", 16)).pack(pady=15)

        self.question_id = tk.Entry(self, width=40)
        self.question_id.pack(pady=6)
        add_placeholder(self.question_id, "ID вопроса")

        tk.Button(self, text="Удалить", command=self.delete_question).pack(pady=12)

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack()

    def delete_question(self):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            question_id = int(self.question_id.get())
        except ValueError:
            messagebox.showerror("Ошибка", "ID вопроса должен быть числом")
            return

        res = requests.delete(
            f"{BASE_URL}/teacher/delete_question/{question_id}",
            headers=headers,
        )
        messagebox.showinfo("Ответ", res.text)
class TeacherTestListFrame(tk.Frame):
    def __init__(self, master, tests):
        super().__init__(master)

        tk.Label(self, text="Мои тесты", font=("Arial", 18)).pack(pady=15)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        if not tests:
            tk.Label(container, text="Нет тестов", font=("Arial", 12)).pack(pady=10)
        else:
            for test in tests:
                row = tk.Frame(container)
                row.pack(fill="x", pady=6)

                tk.Label(
                    row,
                    text=f"{test['title']} (ID: {test['id']})",
                    font=("Arial", 12)
                ).pack(side="left", anchor="w")

                tk.Button(
                    row,
                    text="Результаты",
                    command=lambda test_id=test["id"]: master.switch_frame(
                        lambda m: TeacherResultFrame(m, test_id)
                    )
                ).pack(side="right")

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack(pady=15)


class TeacherResultFrame(tk.Frame):
    def __init__(self, master, test_id):
        super().__init__(master)

        tk.Label(self, text=f"Результаты теста ID={test_id}", font=("Arial", 16)).pack(pady=15)

        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/teacher/result/{test_id}", headers=headers)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        if res.status_code != 200:
            tk.Label(container, text="Ошибка загрузки результатов", font=("Arial", 12)).pack()
        else:
            data = res.json()

            if not data:
                tk.Label(container, text="Нет попыток", font=("Arial", 12)).pack()
            else:
                for item in data:
                    tk.Label(
                        container,
                        text=f"user_id: {item['user_id']} | result: {item['result']} | date: {item['date']}",
                        anchor="w",
                        justify="left"
                    ).pack(fill="x", pady=3)

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack(pady=10)
class StudentResultsFrame(tk.Frame):
    def __init__(self, master, results):
        super().__init__(master)

        tk.Label(self, text="Мои результаты", font=("Arial", 18)).pack(pady=15)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        if not results or isinstance(results, dict):
            message = "Результаты не найдены"
            if isinstance(results, dict):
                message = results.get("Message", results.get("message", message))
            tk.Label(container, text=message, font=("Arial", 12)).pack(pady=10)
        else:
            for item in results:
                row = tk.Frame(container)
                row.pack(fill="x", pady=6)

                title = item.get("название", "Без названия")
                test_id = item.get("test_id")
                best_score = item.get("лучшая попытка", "—")

                tk.Label(
                    row,
                    text=f"{title} (ID: {test_id}) | лучший результат: {best_score}",
                    font=("Arial", 12)
                ).pack(side="left", anchor="w")

                tk.Button(
                    row,
                    text="История попыток",
                    command=lambda t=test_id: master.switch_frame(
                        lambda m: StudentSingleResultFrame(m, t)
                    )
                ).pack(side="right")

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(MainFrame)
        ).pack(pady=15)


class StudentSingleResultFrame(tk.Frame):
    def __init__(self, master, test_id):
        super().__init__(master)

        tk.Label(self, text=f"Попытки по тесту ID={test_id}", font=("Arial", 16)).pack(pady=15)

        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/student/result/{test_id}", headers=headers)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        if res.status_code != 200:
            tk.Label(container, text="Ошибка загрузки результатов", font=("Arial", 12)).pack()
        else:
            data = res.json()

            if not data or isinstance(data, dict):
                message = "Попытки не найдены"
                if isinstance(data, dict):
                    message = data.get("Message", data.get("message", message))
                tk.Label(container, text=message, font=("Arial", 12)).pack(pady=10)
            else:
                for item in data:
                    # у тебя в backend ключ называется "attemtp" с опечаткой
                    attempt_number = item.get("attemtp", "—")
                    result = item.get("result", "—")
                    date = item.get("date", "—")

                    tk.Label(
                        container,
                        text=f"Попытка #{attempt_number} | результат: {result} | дата: {date}",
                        anchor="w",
                        justify="left"
                    ).pack(fill="x", pady=3)

        tk.Button(
            self,
            text="Назад",
            command=lambda: master.switch_frame(
                lambda m: StudentResultsFrame(m, self.load_results())
            )
        ).pack(pady=10)

    def load_results(self):
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/student/result", headers=headers)
        if res.status_code == 200:
            return res.json()
        return []