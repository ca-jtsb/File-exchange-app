import socket
import threading
import os
import ttkbootstrap as ttk
from tkinter import font, scrolledtext

class ServerApp:
    DEFAULT_HOST = '127.0.0.1'
    DEFAULT_PORT = 12345

    def __init__(self):
        self.host = self.DEFAULT_HOST
        self.port = self.DEFAULT_PORT
        self.clients = {}
        self.files_directory = "server_files"
        os.makedirs(self.files_directory, exist_ok=True)
        
        # Initialize the GUI
        self.init_gui()
        self.server_socket = None
        self.active_connections = set()

    def init_gui(self):
        self.root = ttk.Window(themename="vapor")
        self.style = ttk.Style()
        self.set_default_font()

        self.root.title("Server")
        self.root.geometry('680x600')

        # Main Frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Connection Info Frame
        self.conn_info_frame = ttk.LabelFrame(main_frame, text='Connection Information', padding=10)
        self.conn_info_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        # Log Frame
        self.log_frame = ttk.LabelFrame(main_frame, text='Server Log', padding=10)
        self.log_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

        # Labels and Entries
        self.create_labels()
        self.create_log_area()

    def set_default_font(self, font_name='Helvetica', font_size=10, font_weight='bold'):
        default_font = (font_name, font_size, font_weight)
        
        self.style.configure('TLabel', font=default_font)
        self.style.configure('TButton', font=default_font)
        self.style.configure('TEntry', font=default_font)
        self.style.configure('TFrame', font=default_font)
        self.style.configure('TCheckbutton', font=default_font)
        self.style.configure('TRadiobutton', font=default_font)

    def create_labels(self):
        ttk.Label(self.conn_info_frame, text='Address', anchor='center', width=25).grid(row=1, column=1, ipadx=10, ipady=5)
        ttk.Label(self.conn_info_frame, text='Port Number', anchor='center', width=25).grid(row=2, column=1, ipadx=10, ipady=5)
        ttk.Label(self.conn_info_frame, text='Number of Users', anchor="center", width=25).grid(row=3, column=1, ipadx=10, ipady=5)
        ttk.Label(self.conn_info_frame, text='List of Users', anchor='center', width=25).grid(row=4, column=1, ipadx=10, ipady=5)

        self.address_label = ttk.Label(self.conn_info_frame, text=self.host, bootstyle="inverse-primary", relief='sunken', anchor='center', width=25)
        self.address_label.grid(row=1, column=2, ipadx=10, ipady=5)
        
        self.port_label = ttk.Label(self.conn_info_frame, text=self.port, bootstyle="inverse-primary", relief='sunken', anchor='center', width=25)
        self.port_label.grid(row=2, column=2, ipadx=10, ipady=5)
        
        self.number_users_label = ttk.Label(self.conn_info_frame, text="0", bootstyle="inverse-primary", relief='sunken', anchor='center', width=25)
        self.number_users_label.grid(row=3, column=2, ipadx=10, ipady=5)
        
        self.list_users_label = ttk.Label(self.conn_info_frame, text=f"", bootstyle="inverse-primary", relief='sunken', anchor='center', width=25)
        self.list_users_label.grid(row=4, column=2, ipadx=10, ipady=5)

    def create_log_area(self):
        self.log_area = scrolledtext.ScrolledText(self.log_frame, wrap='word', height=15, width=70)
        self.log_area.pack(expand=True, fill='both')

    def log_message(self, message):
        self.log_area.configure(state='normal')  # Enable editing
        self.log_area.insert('end', message + '\n')
        self.log_area.yview('end')
        self.log_area.configure(state='disabled')  # Disable editing

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.number_users_label.config(text="0")
        self.log_message(f"Server started on {self.host}:{self.port}")
        threading.Thread(target=self.accept_clients).start()

    def accept_clients(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            
            if client_address in self.active_connections:
                self.log_message(f"Rejected connection from {client_address}: Already connected")
                client_socket.close()
                continue
            
            self.active_connections.add(client_address)
            self.log_message(f"Connection from {client_address}")
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

    def handle_client(self, client_socket, client_address):
        registered = False
        joined = False
        handle = None

        while True:
            try:
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                command, *params = data.split()
                print(f"Received command: {command}, params: {params}, from {client_address}")

                if command == "/register":
                    if registered:
                        client_socket.sendall("Error: Already registered.".encode())
                    else:
                        handle = params[0]
                        registration_status = self.register_handle(client_socket, handle)
                        if registration_status == "Success":
                            registered = True

                elif command == "/store":
                    if registered:
                        self.store_file(client_socket, params[0])
                    else:
                        client_socket.sendall("Error: Please join the server before storing files.".encode())

                elif command == "/dir":
                    if registered:
                        self.send_directory_list(client_socket)
                    else:
                        client_socket.sendall("Error: Please join the server before requesting directory list.".encode())

                elif command == "/get":
                    if registered:
                        self.send_file(client_socket, params[0])
                    else:
                        client_socket.sendall("Error: Please join the server before requesting files.".encode())

                elif command == "/join":
                    if not joined:
                        self.clients[client_socket] = handle  # Register client with current handle
                        client_socket.sendall("Joined the server successfully.".encode())
                        joined = True
                        self.update_users_text()  # Update the users list when a client joins
                    else:
                        client_socket.sendall("Error: Already joined.".encode())

                elif command == "/leave":
                    if joined:
                        self.clients.pop(client_socket, None)
                        client_socket.sendall("Left the server.".encode())
                        joined = False
                        registered = False
                        handle = None
                        self.update_users_text()  # Update the users list when a client leaves
                    else:
                        client_socket.sendall("Error: Not joined yet.".encode())

                else:
                    client_socket.sendall("Error: Command not found.".encode())

            except Exception as e:
                self.log_message(f"Error: {str(e)}")
                break

        # Clean up after client disconnects
        if handle and handle in self.clients.values():
            self.clients = {cs: h for cs, h in self.clients.items() if h != handle}

        self.active_connections.discard(client_address)  # Use discard to avoid KeyError
        self.update_users_text()
        client_socket.close()


    def register_handle(self, client_socket, handle):
        if handle not in self.clients.values():
            self.clients[client_socket] = handle
            client_socket.sendall(f"Welcome {handle}!".encode())
            self.update_users_text()  # Update UI with new user list
            return "Success"
        else:
            client_socket.sendall("Error: Registration failed. Handle or alias already exists.".encode())
            return "Failure"

    def store_file(self, client_socket, filename):
        file_path = os.path.join(self.files_directory, filename)
        try:
            with open(file_path, 'wb') as file:
                while True:
                    data = client_socket.recv(1024)
                    if b"\r\nEND\r\n" in data:
                        data, _ = data.split(b"\r\nEND\r\n", 1)
                        file.write(data)
                        break
                    file.write(data)
            self.log_message(f"File {filename} stored successfully.")
        except Exception as e:
            client_socket.sendall(f"Error: Failed to store file. {str(e)}".encode())
            self.log_message(f"Error: {str(e)}")

    def send_directory_list(self, client_socket):
        files = os.listdir(self.files_directory)
        if files:
            file_list = "\n".join(files)
            client_socket.sendall(f"Directory list:\n{file_list}".encode())
        else:
            client_socket.sendall("Directory is empty.".encode())

    def send_file(self, client_socket, filename):
        file_path = os.path.join(self.files_directory, filename)
        try:
            if not os.path.exists(file_path):
                client_socket.sendall(f"Error: File '{filename}' not found.".encode())
                return

            with open(file_path, 'rb') as file:
                while chunk := file.read(1024):
                    client_socket.sendall(chunk)
            client_socket.sendall(b"\r\nEND\r\n")
        except Exception as e:
            client_socket.sendall(f"Error: Failed to send file. {str(e)}".encode())
            self.log_message(f"Error: {str(e)}")


    def update_users_text(self):
        number_of_users = len(self.clients)
        self.number_users_label.config(text=number_of_users)
        list_of_users = "\n".join(self.clients.values())
        self.list_users_label.config(text=list_of_users)

    def run(self):
        self.start_server()
        self.root.mainloop()

if __name__ == "__main__":
    app = ServerApp()
    app.run()
