import socket
import os
from datetime import datetime
import ttkbootstrap as ttk
from tkinter import scrolledtext, StringVar, NORMAL, DISABLED, END

class ClientApp:
    DEFAULT_HOST = '0.0.0.0'
    DEFAULT_PORT = 0

    def __init__(self):
        self.host = self.DEFAULT_HOST
        self.port = self.DEFAULT_PORT
        self.client_socket = None
        self.is_registered = False
        self.is_joined = False
        self.setup_gui()
    
    def setup_gui(self):
        # Set up the main application window
        self.app = ttk.Window(themename="superhero")
        self.style = ttk.Style()
        self.set_default_font()
        
        self.app.title("File Exchange Client")
        self.app.geometry("800x650")

        # Main Frame
        self.main_frame = ttk.Frame(self.app)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Connection Info Frame
        self.conn_info_frame = ttk.LabelFrame(self.main_frame, text='Connection Information', padding=10)
        self.conn_info_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.create_labels()
        
        # Input Frame
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

        # Log Frame
        self.log_frame = ttk.LabelFrame(self.main_frame, text='Client Log', padding=10)
        self.log_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')

        # Command Entry and Button
        self.command_label = ttk.Label(self.input_frame, text="Command:")
        self.command_label.pack(side='left', padx=5)

        self.command_entry = ttk.Entry(self.input_frame, width=50)
        self.command_entry.pack(side='left', padx=5)

        self.send_button = ttk.Button(self.input_frame, text="Send", command=self.execute_command)
        self.send_button.pack(side='left', padx=5)

        # ScrolledText for Logs
        self.output_area = scrolledtext.ScrolledText(self.log_frame, state=DISABLED, width=80, height=15)
        self.output_area.pack(expand=True, fill='both')

        # Run the application
        self.app.mainloop()

    def set_default_font(self, font_name='Helvetica', font_size=10, font_weight='bold'):
        # Create a font configuration
        default_font = (font_name, font_size, font_weight)
        
        # Configure styles for various widgets
        self.style.configure('TLabel', font=default_font)
        self.style.configure('TButton', font=default_font)
        self.style.configure('TEntry', font=default_font)
        self.style.configure('TFrame', font=default_font)
        self.style.configure('TCheckbutton', font=default_font)
        self.style.configure('TRadiobutton', font=default_font)

    def create_labels(self):
        ttk.Label(self.conn_info_frame, text='Address', anchor='center', width=25).grid(row=1, column=1, ipadx=10, ipady=5)
        ttk.Label(self.conn_info_frame, text='Port Number', anchor='center', width=25).grid(row=2, column=1, ipadx=10, ipady=5)
        ttk.Label(self.conn_info_frame, text='Status', anchor="center", width=25).grid(row=3, column=1, ipadx=10, ipady=5)
        ttk.Label(self.conn_info_frame, text='User Handle', anchor='center', width=25).grid(row=4, column=1, ipadx=10, ipady=5)

        self.address_label = ttk.Label(self.conn_info_frame, text="0", bootstyle="inverse-primary", relief='sunken', anchor='center', width=25)
        self.address_label.grid(row=1, column=2, ipadx=10, ipady=5)
        
        self.port_label = ttk.Label(self.conn_info_frame, text="0", bootstyle="inverse-primary", relief='sunken', anchor='center', width=25)
        self.port_label.grid(row=2, column=2, ipadx=10, ipady=5)
        
        self.status_label = ttk.Label(self.conn_info_frame, text="Unjoined", bootstyle="inverse-primary", relief='sunken', anchor='center', width=25)
        self.status_label.grid(row=3, column=2, ipadx=10, ipady=5)
        
        self.user_handle_label = ttk.Label(self.conn_info_frame, text="", bootstyle="inverse-primary", relief='sunken', anchor='center', width=25)
        self.user_handle_label.grid(row=4, column=2, ipadx=10, ipady=5)

    def connect_to_server(self, ip, port):
        if self.is_joined:
            self.update_output("Already joined the server.")
            return
        else:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((ip, port))
                self.update_output("Connection to the File Exchange Server is successful!")
                self.update_status("Joined")
                self.is_joined = True
                self.host = ip
                self.port = port
                self.update_labels()
            except Exception as e:
                self.update_output(f"Error: Connection to the Server has failed! Please check IP Address and Port Number. {str(e)}")

    def disconnect_from_server(self):
        if not self.is_joined:
            self.update_output("Error: You have not joined the server yet.")
            return
        
        try:
            if self.client_socket:
                self.client_socket.sendall("/leave".encode())
                self.client_socket.close()
                self.update_output("Connection closed. Thank you!")
                self.update_status("Unjoined")
                self.is_joined = False
                self.is_registered = False
                self.user_handle_label.config(text="")
                self.update_labels()
        except Exception as e:
            self.update_output(f"Error: Disconnection failed. {str(e)}")

    def register_handle(self, handle):
        if not self.is_joined:
            self.update_output("Error: Please join the server before registering.")
            return
        
        if self.is_registered:
            self.update_output("Error: Already registered.")
            return
        
        self.client_socket.sendall(f"/register {handle}".encode())
        response = self.client_socket.recv(1024).decode()
        if "Welcome" in response:
            self.is_registered = True
            self.update_status("Registered")
            self.user_handle_label.config(text=handle)
        self.update_output(response)

    def send_file_to_server(self, filename):
        if not self.is_joined:
            self.update_output("Error: Please join the server before sending files.")
            return

        if os.path.exists(filename):
            try:
                with open(filename, 'rb') as file:
                    self.client_socket.sendall(f"/store {filename}".encode())
                    while True:
                        file_data = file.read(1024)
                        if not file_data:
                            break
                        self.client_socket.sendall(file_data)
                    # Send delimiter to indicate end of file
                    self.client_socket.sendall(b"\r\nEND\r\n")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.update_output(f"User<{timestamp}>: Uploaded {filename}")
            except Exception as e:
                self.update_output(f"Error: Failed to send file. {str(e)}")
        else:
            self.update_output("Error: File not found.")

    def fetch_file_from_server(self, filename):
        if not self.is_joined:
            self.update_output("Error: Please join the server before requesting files.")
            return

        self.client_socket.sendall(f"/get {filename}".encode())
        
        data = self.client_socket.recv(1024)
        if data.startswith(b"Error:"):
            self.update_output(data.decode())
            return

        with open(filename, 'wb') as file:
            while True:
                if b"\r\nEND\r\n" in data:
                    data, _ = data.split(b"\r\nEND\r\n", 1)
                    file.write(data)
                    break
                file.write(data)
                data = self.client_socket.recv(1024)
        
        self.update_output(f"File received from Server: {filename}")

    def request_directory_list(self):
        if not self.is_registered:
            self.update_output("Error: Please join the server before requesting the directory list.")
            return

        try:
            self.client_socket.sendall("/dir".encode())
            response = self.client_socket.recv(1024).decode()
            self.update_output(f"Files in server:\n{response}")
        except Exception as e:
            self.update_output(f"Error: Failed to retrieve directory list. {str(e)}")

    def update_output(self, message):
        self.output_area.config(state=NORMAL)
        self.output_area.insert(END, message + "\n")
        self.output_area.config(state=DISABLED)

    def update_status(self, status):
        self.status_label.config(text=status)

    def update_labels(self):
        self.address_label.config(text=self.host)
        self.port_label.config(text=str(self.port))
        if self.is_joined:
            self.status_label.config(text="Joined")
        else:
            self.status_label.config(text="Unjoined")

    def execute_command(self):
        command = self.command_entry.get()
        tokens = command.split()

        if not tokens:
            self.update_output("Error: Command not found.")
            return

        cmd = tokens[0]
        if cmd == '/join' and len(tokens) == 3:
            self.connect_to_server(tokens[1], int(tokens[2]))
            
        elif cmd == '/leave':
            self.disconnect_from_server()
        elif cmd == '/register' and len(tokens) == 2:
            self.register_handle(tokens[1])
        elif cmd == '/store' and len(tokens) == 2:
            self.send_file_to_server(tokens[1])
        elif cmd == '/dir':
            self.request_directory_list()
        elif cmd == '/get' and len(tokens) == 2:
            self.fetch_file_from_server(tokens[1])
        elif cmd == '/?':
            self.display_help()
        else:
            self.update_output("Error: Command not found or incorrect parameters.")

    def display_help(self):
        help_message = (
            "Available Commands:\n"
            "/join <server_ip_add> <port>\n"
            "/leave\n"
            "/register <handle>\n"
            "/store <filename>\n"
            "/dir\n"
            "/get <filename>\n"
            "/?\n"
        )
        self.update_output(help_message)

if __name__ == "__main__":
    ClientApp()
