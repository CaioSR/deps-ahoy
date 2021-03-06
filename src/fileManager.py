from Status import StatusTypes
import os
import csv
import shutil
import configparser 

class FileManager:
    """
    Manages file reading/creation
    """
    f_dir = None
    p_dir = None

    def __init__(self, f_dir, p_dir, proj):
        """
        Replaces + with / to create directories
        """
        proj = proj.replace('/','+')

        if f_dir[-1] == '/':
            self.f_dir = f_dir
        else:
            self.f_dir = f_dir + '/'

        if p_dir[-1] == '/':
            self.p_dir = p_dir
        else:
            self.p_dir = p_dir + '/'

        self.verifyDirectories(proj)
        
    def verifyDirectories(self, proj):
        """
        Verify if folders exist, if not, create them.
        """
        if '/' in proj:
            proj = proj.replace('/', '+')

        index = self.p_dir.find(proj)
        if index != -1:
            self.p_dir = self.p_dir[:index]

        index = self.f_dir.find(proj)
        if index != -1:
            self.f_dir = self.f_dir[:index]

        try:
            os.mkdir(self.p_dir)
            os.mkdir(self.f_dir)
        except FileExistsError:
            pass

        try:
            self._resetState(proj)
            print('All status to closed')

        except FileNotFoundError:
            print('First Run')

            os.mkdir(self.p_dir + proj)
            os.mkdir(self.p_dir + proj + '/artifacts')
            os.mkdir(self.f_dir + proj)

        self.p_dir = self.p_dir + proj
        self.f_dir = self.f_dir + proj

    def verifyConfig(self, repo, proj, depth, f_dir):
        """
        Manages config file to resume operation if needed
        """
        if not os.path.exists(self.p_dir + '/config.ini'):
            config = configparser.ConfigParser()
            config.read('config.ini')
            config.add_section('Operation Atributes')
            config.set('Operation Atributes', 'repository', repo)
            config.set('Operation Atributes', 'project_link', proj)
            config.set('Operation Atributes', 'maximum_depth', str(depth))
            config.set('Operation Atributes', 'end_directory', f_dir)

            with open(self.p_dir + '/config.ini', 'w', newline='') as writeConfig:
                config.write(writeConfig)
            writeConfig.close()

    def addArtifact(self, artifact):
        """
        Adds a new artifact in the Nodes.csv
        """
        try:
            found = False
            with open(self.p_dir + '/Nodes.csv', 'r', newline='') as readFile:
                for line in readFile:
                    if line[0] == artifact: #line ****
                        found = True
                        break

            readFile.close()

            if not found:
                with open(self.p_dir + '/Nodes.csv', 'a', newline='') as writeFile:
                    writer  = csv.writer(writeFile)
                    writer.writerow([artifact])

                writeFile.close()
        except:
            with open(self.p_dir + '/Nodes.csv', 'w', newline='') as writeFile:
                writer  = csv.writer(writeFile)
                writer.writerow([artifact])

            writeFile.close()

    def addLinks(self, artifact, dependencies):
        """
        Adds a new link in the Links.csv
        """
        with open(self.p_dir + '/Links.csv', 'a', newline='') as writeFile:
            writer = csv.writer(writeFile)
            for dependency in dependencies:
                link = [artifact, dependency]
                writer.writerow(link)

        writeFile.close()

    def initialize(self, artifact,depth):
        """
        Writes the first line in Progress.csv
        """
        with open(self.p_dir + '/Progress.csv', 'a', newline='') as writeFile:
            writer = csv.writer(writeFile)
            writer.writerow([depth,artifact,'Initialized','Null','open'])

        writeFile.close()

    def setStatus(self, artifact, status):
        """
        Updates the status of a artifact
        """
        with open(self.p_dir + '/Progress.csv', 'r') as readFile, open(self.p_dir + '/Progress_temp.csv', 'w', newline='') as writeFile:
            reader = csv.reader(readFile)
            writer = csv.writer(writeFile)
            for line in reader:
                if line[1] == artifact:
                    line[2] = status
                    line[3] = 'Null'
                    writer.writerow(line)
                else:
                    writer.writerow(line)

        readFile.close()
        writeFile.close()
        os.remove(self.p_dir + '/Progress.csv')
        os.rename(self.p_dir + '/Progress_temp.csv', self.p_dir + '/Progress.csv')

    def setCurrentPage(self, artifact, page):
        """
        Updates the page of the current artifact's usages search
        """
        with open(self.p_dir + '/Progress.csv', 'r') as readFile, open(self.p_dir + '/Progress_temp.csv', 'w', newline='') as writeFile:
            reader = csv.reader(readFile)
            writer = csv.writer(writeFile)
            for line in reader:
                if line[1] == artifact:
                    line[3] = page
                    writer.writerow(line)
                else:
                    writer.writerow(line)

        readFile.close()
        writeFile.close()
        os.remove(self.p_dir + '/Progress.csv')
        os.rename(self.p_dir + '/Progress_temp.csv', self.p_dir + '/Progress.csv')

    def setCurrentArtifact(self, artifact, relation, current):
        """
        Updates which type of artifact its currently being search, and what is it.
        """
        with open(self.p_dir + '/Progress.csv', 'r') as readFile, open(self.p_dir + '/Progress_temp.csv', 'w', newline='') as writeFile:
            reader = csv.reader(readFile)
            writer = csv.writer(writeFile)
            for line in reader:
                if line[1] == artifact:
                    if relation == 'd':
                        line[2] = StatusTypes.verifyingDependency
                    elif relation == 'u':
                        line[2] = StatusTypes.verifyingUsage
                    line[3] = current
                    writer.writerow(line)
                else:
                    writer.writerow(line)

        readFile.close()
        writeFile.close()
        os.remove(self.p_dir + '/Progress.csv')
        os.rename(self.p_dir + '/Progress_temp.csv', self.p_dir + '/Progress.csv')

    def writeDependency(self, artifact, dependency):
        """
        Updates the artifacts dependencies list. (can be erased after procedure is finished)
        """
        file = artifact.replace('/','+')
        file = self.p_dir + '/artifacts/['+file+']Dependencies.csv'

        try:
            found = False
            with open(file, 'r') as readFile:
                for line in readFile:
                    if line[0] == dependency:
                        found = True
                        break

            readFile.close()

            if not found:
                with open(file, 'a', newline='') as writeFile:
                    writer = csv.writer(writeFile)
                    writer.writerow([dependency])

                writeFile.close()

        except:
            with open(file, 'w', newline='') as writeFile:
                writer = csv.writer(writeFile)
                writer.writerow([dependency])

            writeFile.close()

    def writeUsage(self, artifact, usage):
        """
        Updates the artifacts usages list. (can be erased after procedure is finished)
        """
        file = artifact.replace('/','+')
        file = self.p_dir + '/artifacts/['+file+']Usages.csv'

        try:
            found = False
            with open(file, 'r') as readFile:
                for line in readFile:
                    if line[0] == usage:
                        found = True
                        break

            readFile.close()

            if not found:
                with open(file, 'a', newline='') as writeFile:
                    writer = csv.writer(writeFile)
                    writer.writerow([usage])

                writeFile.close()

        except:
            with open(file, 'w', newline='') as writeFile:
                writer = csv.writer(writeFile)
                writer.writerow([usage])

            writeFile.close()

    def checkProgress(self, artifact):
        """
        Check if artifact is in progress
        """
        try:
            with open(self.p_dir + '/Progress.csv', 'r') as readFile:
                reader = csv.reader(readFile)
                for line in reader:
                    if line[1] == artifact:
                        return True
                return False
        except:
            return False

    def getProgress(self, artifact):
        """
        Get the artifact's progress
        """
        with open(self.p_dir + '/Progress.csv', 'r') as readFile:
            reader = csv.reader(readFile)
            for line in reader:
                if line[1] == artifact:
                    return line

        readFile.close()

    def readDependencies(self, artifact):
        """
        Reads the artifact's dependencies one by one
        """
        file = artifact.replace('/','+')
        file = self.p_dir + '/artifacts/['+file+']Dependencies.csv'

        with open(file, 'r') as readFile:
            for line in readFile:
                yield line.strip('\n')

        return

    def readUsages(self, artifact):
        """
        Reads the artifact's usages one by one
        """
        file = artifact.replace('/','+')
        file = self.p_dir + '/artifacts/['+file+']Usages.csv'

        with open(file, 'r') as readFile:
            for line in readFile:
                yield line.strip('\n')

        return

    def switchState(self, artifact):
        """
        Switch current artifact's state to open or closed
        """
        with open(self.p_dir + '/Progress.csv', 'r') as readFile, open(self.p_dir + '/Progress_temp.csv', 'w', newline='') as writeFile:
            reader = csv.reader(readFile)
            writer = csv.writer(writeFile)
            for line in reader:
                if line[1] == artifact:
                    if line[4] == 'closed':
                        line[4] = 'open'
                    else:
                        line[4] = 'closed'
                    writer.writerow(line)
                else:
                    writer.writerow(line)

        readFile.close()
        writeFile.close()
        os.remove(self.p_dir + '/Progress.csv')
        os.rename(self.p_dir + '/Progress_temp.csv', self.p_dir + '/Progress.csv')

    def _resetState(self,proj):
        """
        Resets the state of every artifact
        """
        p_dir = self.p_dir + proj

        with open(p_dir + '/Progress.csv', 'r') as readFile, open(p_dir + '/Progress_temp.csv', 'w', newline='') as writeFile:
            reader = csv.reader(readFile)
            writer = csv.writer(writeFile)
            for line in reader:
                line[4] = 'closed'
                writer.writerow(line)

        readFile.close()
        writeFile.close()
        os.remove(p_dir + '/Progress.csv')
        os.rename(p_dir + '/Progress_temp.csv', p_dir + '/Progress.csv')

    def moveToFinal(self):
        """
        Move the Nodes.csv and Links.csv to the folder of the definitive files.
        """
        shutil.move(self.p_dir + '/Nodes.csv', self.f_dir)
        shutil.move(self.p_dir + '/Links.csv', self.f_dir)