import os

def new_project(project_name: str):
    """
    可以进入https://smith.langchain.com/o/8dc641fc-f638-4cb6-a914-29d857a5760c查看, github登录
    :param project_name:
    :return:
    """
    os.environ["LANGSMITH_PROJECT"] = project_name