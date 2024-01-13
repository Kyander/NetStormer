from terminal.data import TerminalData
from db.populate import ProjectDb
import os
import shutil


class ProjectManager:
    def __init__(self):
        self.db_data_dir = "{}/db/data/".format(TerminalData.root_dir)
        self.project_root = "{}/projects/".format(TerminalData.root_dir)
        self.project_db_dir = "{}/db/data/projects/".format(TerminalData.root_dir)
        self.internal_db_dir = "{}/db/data/internal/".format(TerminalData.root_dir)
        if not os.path.exists(self.project_root):
            os.mkdir(self.project_root)

    def create_project(self, name, description="No Description", config="No Config"):
        print("Creating project : {}".format(name))
        if os.path.exists("{}{}".format(self.project_root, name)) or os.path.exists("{}{}".format(self.project_db_dir, name)):
            print("Project \"{}\" already exists, delete it or user another name.".format(name))
            return 0
        if not os.path.exists(self.project_db_dir):
            os.mkdir(self.project_db_dir)
        if not os.path.exists(self.internal_db_dir):
            os.mkdir(self.internal_db_dir)
        os.mkdir("{}{}".format(self.project_root, name))
        os.mkdir("{}{}".format(self.project_db_dir, name))
        project_db = ProjectDb()
        project_db.create_sqlite_db(name, description, config)
        print("Done!")

    def delete_project(self, name):
        project_db = ProjectDb()
        if not project_db.exists(name):
            print("Project {} does not exist".format(name))
            return 0
        print("Warning : You are about to delete project {}".format(name))
        answer = input("Do you wish to proceed? (y/n) ")
        if answer.lower() == "y":
            print("Deleting project directory...".format(name))
            shutil.rmtree("{}{}".format(self.project_root, name))
            print("Delete the project database files...")
            shutil.rmtree("{}{}".format(self.project_db_dir, name))
            print("Deleting the project from the main database...")
            project_db.delete_project(name)
            print("Done!")
            if TerminalData.current_project == name:
                TerminalData.current_project = "none"
        else:
            return 0

    def list_projects(self):
        print("Listing all projects...\n")
        project_db = ProjectDb()
        projects = project_db.list_all_projects()
        for project in projects:
            print(project[0])
        print("\nDone!")

    def select_current_project(self, name):
        project_db = ProjectDb()
        if not project_db.exists(name):
            print("Project {} does not exist".format(name))
            return 0
        print("Switching to project {}...".format(name))
        TerminalData.current_project = name
        print("Done!")

    def get_project_info(self, name):
        project_db = ProjectDb()
        if not project_db.exists(name):
            print("Project {} does not exist".format(name))
            return 0
        print("Getting project info...")
        results = project_db.get_project_info(name)
        print("Project Name : {}".format(results[0][0]))
        print("Project Description : {}".format(results[0][1]))
        print("Project Config Path : {}".format(results[0][2]))
