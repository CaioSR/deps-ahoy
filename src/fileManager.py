import csv
import os

class FileManager:
    f_dir = None
    p_dir = None

    def __init__(self, f_dir, p_dir, proj):
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
        try:
            self.defaultStatus(proj)
            print('All status to closed')
        except:
            print('First Run')

            os.mkdir(self.p_dir)
            os.mkdir(self.p_dir + proj)
            os.mkdir(self.p_dir + proj + '/modules')
            os.mkdir(self.f_dir)
            os.mkdir(self.f_dir + proj)

        self.p_dir = self.p_dir + proj
        self.f_dir = self.f_dir + proj

    def addLinks(self, module, dependencies):

        modules = [module]
        for dependency in dependencies:
            modules.append(dependency[2])

        with open(self.p_dir + '/Links.csv', 'a', newline='') as writeFile:
            writer = csv.writer(writeFile)
            writer.writerow(modules)

        writeFile.close()

    def addModule(self, module):

        try:
            found = False
            with open(self.p_dir + '/Nodes.csv', 'r', newline='') as readFile:
                for line in readFile:
                    if line[0] == module:
                        found = True
                        break

            readFile.close()

            if not found:
                with open(self.p_dir + '/Nodes.csv', 'a', newline='') as writeFile:
                    writer  = csv.writer(writeFile)
                    writer.writerow([module])

                writeFile.close()
        except:
            with open(self.p_dir + '/Nodes.csv', 'w', newline='') as writeFile:
                writer  = csv.writer(writeFile)
                writer.writerow([module])

            writeFile.close()

    def initialize(self, module,depth):

        with open(self.p_dir + '/Progress.csv', 'a', newline='') as writeFile:
            writer = csv.writer(writeFile)
            writer.writerow([depth,module,'Initialized','Null','open'])

        writeFile.close()

    def setState(self, module, state):

        with open(self.p_dir + '/Progress.csv', 'r') as readFile, open(self.p_dir + '/Progress_temp.csv', 'w', newline='') as writeFile:
            reader = csv.reader(readFile)
            writer = csv.writer(writeFile)
            for line in reader:
                if module == line[1]:
                    line[2] = state
                    line[3] = 'Null'
                    writer.writerow(line)
                else:
                    writer.writerow(line)

        readFile.close()
        writeFile.close()
        os.remove(self.p_dir + '/Progress.csv')
        os.rename(self.p_dir + '/Progress_temp.csv', self.p_dir + '/Progress.csv')

    def setCurrentPage(self, module, page):

        with open(self.p_dir + '/Progress.csv', 'r') as readFile, open(self.p_dir + '/Progress_temp.csv', 'w', newline='') as writeFile:
            reader = csv.reader(readFile)
            writer = csv.writer(writeFile)
            for line in reader:
                if module == line[1]:
                    line[3] = page
                    writer.writerow(line)
                else:
                    writer.writerow(line)

        readFile.close()
        writeFile.close()
        os.remove(self.p_dir + '/Progress.csv')
        os.rename(self.p_dir + '/Progress_temp.csv', self.p_dir + '/Progress.csv')

    def setCurrent(self, module, relation, current):

        with open(self.p_dir + '/Progress.csv', 'r') as readFile, open(self.p_dir + '/Progress_temp.csv', 'w', newline='') as writeFile:
            reader = csv.reader(readFile)
            writer = csv.writer(writeFile)
            for line in reader:
                if module == line[1]:
                    if relation == 'd':
                        line[2] = 'Verifying dependency'
                    elif relation == 'u':
                        line[2] = 'Verifying usage'
                    line[3] = current
                    writer.writerow(line)
                else:
                    writer.writerow(line)

        readFile.close()
        writeFile.close()
        os.remove(self.p_dir + '/Progress.csv')
        os.rename(self.p_dir + '/Progress_temp.csv', self.p_dir + '/Progress.csv')

    def setUsage(self, module, usage):

        file = module.replace('/','+')
        file = self.p_dir + '/Modules/['+file+']Usages.csv'

        try:
            found = False
            with open(file, 'r') as readFile:
                for line in readFile:
                    if usage == line:
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

    def setDependency(self, module, dependency):

        if dependency != 'None':
            dependency = dependency[2]

        file = module.replace('/','+')
        file = self.p_dir + '/Modules/['+file+']Dependencies.csv'

        try:
            found = False
            with open(file, 'r') as readFile:
                for line in readFile:
                    if dependency == line:
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

    def checkProgress(self, module):

        try:
            with open(self.p_dir + '/Progress.csv', 'r') as readFile:
                reader = csv.reader(readFile)
                for line in reader:
                    if module == line[1]:
                        return True
                return False
        except:
            return False

    def getProgress(self, module):

        with open(self.p_dir + '/Progress.csv', 'r') as readFile:
            reader = csv.reader(readFile)
            for line in reader:
                if module == line[1]:
                    return line

        readFile.close()

    def getDependencies(self, module):
        file = module.replace('/','+')
        file = self.p_dir + '/Modules/['+file+']Dependencies.csv'

        with open(file, 'r') as readFile:
            for line in readFile:
                yield line.strip('\n')

        return

    def getUsages(self, module):

        file = module.replace('/','+')
        file = self.p_dir + '/Modules/['+file+']Usages.csv'

        with open(file, 'r') as readFile:
            for line in readFile:
                yield line.strip('\n')

        return

    def switchStatus(self, module):

        with open(self.p_dir + '/Progress.csv', 'r') as readFile, open(self.p_dir + '/Progress_temp.csv', 'w', newline='') as writeFile:
            reader = csv.reader(readFile)
            writer = csv.writer(writeFile)
            for line in reader:
                if module == line[1]:
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

    def defaultStatus(self,proj):
        p_dir = self.p_dir + proj
        f_dir = self.f_dir + proj

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

    def copyToFinal(self):
        shutil.copy(self.p_dir + '/Nodes.csv', self.f_dir)
        shutil.copy(self.p_dir + '/Links.csv', self.f_dir)