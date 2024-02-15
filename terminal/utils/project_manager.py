from terminal.data import TerminalData
from db.populate import ProjectDb
import os
import shutil


class ProjectManager:
    def __init__(self) -> None:
        self.db_data_dir = "{}/db/data/".format(TerminalData.root_dir)
        self.project_root = "{}/projects/".format(TerminalData.root_dir)
        self.project_db_dir = "{}/db/data/projects/".format(TerminalData.root_dir)
        self.internal_db_dir = "{}/db/data/internal/".format(TerminalData.root_dir)
        if not os.path.exists(self.project_root):
            os.mkdir(self.project_root)

    def create_project(self, name: str, description: str = "No Description", config: str = "No Config") -> None:
        print("Creating project : {}".format(name))
        if os.path.exists("{}{}".format(self.project_root, name)) or os.path.exists("{}{}".format(self.project_db_dir, name)):
            print("Project \"{}\" already exists, delete it or user another name.".format(name))
            return None
        if not os.path.exists(self.project_db_dir):
            os.mkdir(self.project_db_dir)
        if not os.path.exists(self.internal_db_dir):
            os.mkdir(self.internal_db_dir)
        os.mkdir("{}{}".format(self.project_root, name))
        os.mkdir("{}{}".format(self.project_db_dir, name))
        project_db = ProjectDb()
        project_db.create_sqlite_db(name, description, config)
        print("Done!")
        return None

    def delete_project(self, name: str) -> None:
        project_db = ProjectDb()
        if not project_db.exists(name):
            print("Project {} does not exist".format(name))
            return None
        print("Warning : You are about to delete project {}".format(name))
        answer = input("Do you wish to proceed? (y/n) ")
        if answer.lower() == "y":
            print("Deleting {} project directory...".format(name))
            shutil.rmtree("{}{}".format(self.project_root, name))
            print("Delete the project database files...")
            shutil.rmtree("{}{}".format(self.project_db_dir, name))
            print("Deleting the project from the main database...")
            project_db.delete_project(name)
            print("Done!")
            if TerminalData.current_project == name:
                TerminalData.current_project = "none"
        else:
            return None

    def list_projects(self) -> None:
        print("Listing all projects...\n")
        project_db = ProjectDb()
        projects = project_db.list_all_projects()
        for project in projects:
            print(project[0])
        print("\nDone!")
        return None

    def select_current_project(self, name: str) -> None:
        project_db = ProjectDb()
        if not project_db.exists(name):
            print("Project {} does not exist".format(name))
            return None
        print("Switching to project {}...".format(name))
        TerminalData.current_project = name
        print("Done!")
        return None

    def get_project_info(self, name: str) -> None:
        project_db = ProjectDb()
        if not project_db.exists(name):
            print("Project {} does not exist".format(name))
            return None
        print("Getting project info...")
        results = project_db.get_project_info(name)
        print(results)
        print("Project Name : {}".format(results[0][0]))
        print("Project Description : {}".format(results[0][1]))
        print("Project Config Path : {}".format(results[0][2]))
        return None
