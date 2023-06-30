import os
import requests
from bs4 import BeautifulSoup

class Jenkins_Scaper():
    def __init__(self, path):
        self.path = path
        self.req = requests.get(self.path)
        self.soup = BeautifulSoup(self.req.content, "html.parser")
        self.file_dict = {}

    def get_branch_list(self):
        branch_list = []
        table = self.soup.select_one('.jenkins-table')
        branches = table.findAll('a')
        for link in branches:
            path = os.path.normpath(link['href'])
            encoded = path.split(os.sep)[1]
            decoded = encoded.replace('%252F', '/')
            branch_list.append(decoded)
            branch_list = list(set(branch_list))
            branch_list.sort()
        return branch_list

    def get_build_list(self, path):
        build_list = []
        req = requests.get(path)
        soup = BeautifulSoup(req.content, "html.parser")
        b = soup.findAll("a",{"class":"tip model-link inside build-link display-name"})
        for link in b:
            path = os.path.normpath(link['href'])
            build_list.append(path.split(os.sep)[-1])
        return build_list
    
    
    def get_file_list(self, path):
        file_dict = {}
        file_list = []
        req = requests.get(path)
        soup = BeautifulSoup(req.content, "html.parser")
        f = soup.findAll('a',{"rel":"nofollow noopener noreferrer"})
        for line in f:
            path = line['href']
            file_list.append(path.split(os.sep)[-1])
            self.file_dict.update({path.split(os.sep)[-1]: path})
        sorted_files = sorted(self.file_dict.items())
        return file_list

    def get_change_list(self, path):
        change_list = []
        req = requests.get(path)
        soup = BeautifulSoup(req.content, "html.parser")
        ol = soup.select_one("ol")
        if ol:
            for text in ol:
                t = text.get_text()
                change_list.append(t)
        return change_list
    
    def download(self, file, path):
        pass
        # TODO - move download function from main.py to here
