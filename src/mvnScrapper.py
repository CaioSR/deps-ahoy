from UrlHandler import UrlHandler
from FileManager import FileManager
from Status import StatusTypes
import requests
import re

class MVNScrapper:
    """
    This class implements the methods needed to scrap dependencies graphs from MVNRepository
    """
    def __init__(self):
        self._fileManager = None
        self._maxDepth = None

    def scrapper(self, project, max_depth, f_dir, p_dir):
        """
        Called by the ScrapperCaller class. It handles the overall execution.
        """
        p = self._separateV(project, getRoot = True, getVersion = True, getArtifact = True)
        project_url = p[0]
        version = p[1]
        artifact = p[2]
        self._maxDepth = max_depth
        self._fileManager = FileManager(f_dir, p_dir, artifact)
        self._fileManager.verifyConfig('MVNRepository', project_url+version, max_depth, f_dir)
        self._scrap(project_url, 0, target_version = version) #it doesn't exit after its finished.
        print('Procedure is done')
        self._fileManager.moveToFinal()

    def fetchDependencies(self, url, artifact):
        """
        With the given url, looks for the artifacts dependencies
        """
        soup = UrlHandler.getSoup(url)

        found = False
        scope = False
        dependencies = []

        for tag in soup.find_all('a'):
            link = tag.get('href')
            
            if scope:
                if 'twitter' in link:
                    scope = False
                if '/artifact/' in link:
                    if not tag.get('class'):
                        found = False
                    if not found and tag.get('class') and len(tag.get('class')) > 1 and tag.get('class')[0] == 'vbtn':
                        dependencies.append(link[10:])
                        if self._fileManager:
                            self._fileManager.writeDependency(artifact, link[10:])
                        found = True

            if '#buildr' in link:
                scope = True

        return dependencies

    def fetchUsages(self, url, artifact, page=None):
        """
        With the given url, looks for the artifacts usages while handling pages
        """
        soup = UrlHandler.getSoup(url)

        artifact_root = self._separateV(artifact, getRoot = True)[0]
        scala = re.search(r'_[0-9]\.[0-9][0-9]', artifact_root)
        if scala:
            artifact_root = artifact_root[:-5]
        usages = []
        previous = ''
        scope = False
        end = False
        next_page = 0
        current_page = 0

        if not page:
            print('Page 1')
        else:
            usages_page_link = url + '?p=' + page
            print("Continued on page " + page)
            soup = UrlHandler.getSoup(usages_page_link)
            current_page = int(page)
            if self._fileManager:
                self._fileManager.setCurrentPage(artifact, page)
            page = None

        while not end:

            for tag in soup.find_all('a'):
                link = tag.get('href')

                if scope:

                    if '?p=' in link:
                        next_page = int(link[3:])

                        if next_page > current_page:
                            scope = False
                            usages_page_link = url + link
                            soup = UrlHandler.getSoup(usages_page_link)
                            current_page = int(link[3:])
                            print('Page',current_page)
                            if self._fileManager:
                                self._fileManager.setCurrentPage(artifact, current_page)
                            break

                    elif '/tags' in link:
                        end = True
                        scope = False

                        break

                    elif '/artifact/' in link:
                        if link == previous:
                            if link not in usages:
                                usages.append(link[10:])
                                if self._fileManager:
                                    self._fileManager.writeUsage(artifact,link[10:])

                        previous = link

                if artifact_root in link:
                    scope = True

        return usages

    def fetchVersions(self, url):
        """
        Get the artifacts version (or versions if there are multiple)
        """
        soup = UrlHandler.getSoup(url)

        versions = []
        multiple_versions = False
        for tag in soup.find_all('a'):
            if tag.get('class') and tag.get('class')[0] == 'vsc':
                multiple_versions = True
                break

        if multiple_versions:
            for tag in soup.find_all('a', class_='vsc'):
                versions.append(tag.get('href'))
        else:
            for tag in soup.find_all('a', class_='vbtn'):
                versions.append(tag.get('href'))

        return versions

    def getUsageVersion(self, url, lookForDependency):
        """
        Open each usage's versions to check if one of their dependencies have the source artifact with 
        the given version that stated that this usage is using it
        """
        artifact_root = url[url.find('/artifact/'):][10:]

        versions = self.fetchVersions(url)
        
        if len(versions) == 0:
            return None

        multiple_versions = False
        if '/artifact/' in versions[0]:
            multiple_versions = True
        
        iteration = 0
        for vers in versions:
            iteration+=1
            #if multiple /artifact/abc/xyz/123
            #if not xyz/123

            if multiple_versions:
                vers = vers[10:]
                artifact = vers
            
            vers = vers[vers.find('/'):] 
            print("Currently on {}" .format(vers))

            if not multiple_versions:
                artifact = artifact_root + vers

            result = self._searchDependency("https://mvnrepository.com/artifact/"+artifact, lookForDependency)

            if result:
                print("Correct version is {}" .format(vers))
                return vers

            if iteration == 100:
                """
                After checking 100 versions, it gives up to save time.
                """
                return None

        return None


    def _scrap(self, root_url, depth, target_version = None, lookForDependency = None):
        """
        This is the main recursive method to handle the scrapping
        """
        if target_version:
            version = target_version

        artifact_root = root_url[root_url.find('/artifact'):][10:]

        if not target_version:
            print("Looking for correct usage version")

            try:
                version = self.getUsageVersion(root_url, lookForDependency)

            except requests.exceptions.HTTPError as e:
                self._fileManager.initialize(artifact_root,depth)
                print("---------ERRO--------\n",e,"\n---------------------\nSetting {} to Error Status" .format(artifact_root))
                self._fileManager.setStatus(artifact_root, StatusTypes.error)
                return

            if not version:
                return
            elif version.count('/') == 2:
                root_url = root_url.split('/')
                root_url = '/'.join(root_url[:-1])
                artifact_root = artifact_root[:artifact_root.find('/')]

        artifact = artifact_root+version
        print("Current artifact:", artifact)

        inProgress = self._fileManager.checkProgress(artifact)

        if not inProgress:
            print('New artifact')

            self._fileManager.initialize(artifact,depth) #Status Initialized !! MUDAR !!!

            try:
                self._getDependencies(root_url+version, artifact)
            except requests.exceptions.HTTPError as e:
                print("---------ERRO--------\n",e,"\n---------------------\nSetting {} to Error Status" .format(artifact))
                self._fileManager.setStatus(artifact, StatusTypes.error)
                return

            depth+=1
            if depth < self._maxDepth:

                self._getUsages(root_url+version+'/usages', artifact)
                self._verifyDependencies(artifact, depth)
                self._verifyUsages(artifact, depth)

            else:
                print("Depth too high")

            self._fileManager.setStatus(artifact, StatusTypes.complete)
            return

        elif inProgress:
            print('artifact in progress')

            mod = self._fileManager.getProgress(artifact)
            progress = mod[2]
            depth = int(mod[0])
            state = mod[4]

            #if Not Complete and No Error
            if progress != StatusTypes.complete and progress != StatusTypes.error:
                if state == 'closed':
                    
                    #Its now Open
                    self._fileManager.switchState(artifact)

                    #If Getting Depencies or was only Initialized
                    if progress == StatusTypes.gettingDependencies or progress == StatusTypes.initialized:
                        print('Returned to get dependencies')

                        self._getDependencies(root_url+version, artifact)

                        depth+=1
                        if depth < self._maxDepth:

                            self._getUsages(root_url+version+'/usages', artifact)
                            self._verifyDependencies(artifact, depth)
                            self._verifyUsages(artifact, depth)

                        else:
                            print("Depth too high")

                        self._fileManager.setStatus(artifact, StatusTypes.complete)
                        return

                    #If Getting usages or was only done with looking for Dependencies
                    if progress == StatusTypes.gettingUsages or progress == StatusTypes.doneDependencies:
                        depth+=1
                        if depth < self._maxDepth:

                            print('Returned to getting usages')
                            currentPage = mod[3]
                            if currentPage == 'Null':
                                print('Page count error. Returning to first page')
                                currentPage = '1'
                            else:
                                print('Current usage page: {}' .format(currentPage))

                            self._getUsages(root_url+version+'/usages', artifact, page = currentPage)
                            self._verifyDependencies(artifact, depth)
                            self._verifyUsages(artifact, depth)

                        else:
                            print("Depth too high")

                        self._fileManager.setStatus(artifact, StatusTypes.complete)
                        return

                    #if Verifying Dependencies or was only done with looking Usages
                    if progress == StatusTypes.verifyingDependency or progress == StatusTypes.doneUsages:
                        depth+=1
                        if depth < self._maxDepth:

                            print('Returned to verifying dependencies')
                            currentDependency = mod[3]
                            print('Current dependency: {}' .format(currentDependency))

                            self._verifyDependencies(artifact, depth, current = currentDependency)
                            self._verifyUsages(artifact, depth)

                        else:
                            print("Depth too high")

                        self._fileManager.setStatus(artifact, StatusTypes.complete)
                        return

                    #If Verifying Usages
                    if progress == StatusTypes.verifyingUsage:
                        depth+=1
                        if depth < self._maxDepth:

                            print('Returned to verifying usages')
                            currentUsage = mod[3]
                            print('Current usage: {}' .format(currentUsage))

                            self._verifyUsages(artifact, depth, current = currentUsage)

                        else:
                            print("Depth too high")

                        self._fileManager.setStatus(artifact, StatusTypes.complete)
                        return
                else:
                    #If its closed, then its already open. Close artifact
                    print('Artifact', artifact, 'Already Open')
                    return
            else:
                #If its complete, then close.
                print('Artifact', artifact, 'Already Veryfied')
                return



    def _searchDependency(self, url, dependency):
        """
        It looks for the dependency in an artifact's page
        """
        soup = UrlHandler.getSoup(url)

        for tag in soup.find_all('a'):
            link = tag.get('href')
            if link[10:] == dependency:
                return True

        return False

    def _saveDependencies(self, artifact, dependencies):
        """
        Writes the dependencies (Nodes and Links)
        """
        self._fileManager.addArtifact(artifact)
        for dependency in dependencies:
            self._fileManager.addArtifact(dependency)
        self._fileManager.addLinks(artifact, dependencies)

        print('Updated nodes and links')

    def _getDependencies(self, url, artifact):
        """
        Opens the URL and retrieves the dependencies
        """
        self._fileManager.setStatus(artifact, StatusTypes.gettingDependencies)
        dependencies = self.fetchDependencies(url, artifact)

        if len(dependencies) == 0:
            self._fileManager.writeDependency(artifact, 'None')

        self._saveDependencies(artifact, dependencies)
        self._fileManager.setStatus(artifact, StatusTypes.doneDependencies)
        print('There are {} dependencies in the artifact {}' .format(len(dependencies), artifact))

    def _getUsages(self, url, artifact, page = None):
        """
        Opens the URL and retrieves the usages
        """
        self._fileManager.setStatus(artifact, StatusTypes.gettingUsages)
        usages = self.fetchUsages(url, artifact, page = page)

        if len(usages) == 0:
            self._fileManager.writeUsage(artifact, 'None')

        self._fileManager.setStatus(artifact, StatusTypes.doneUsages)
        print('There are {} usages in the artifact {}' .format(len(usages), artifact))

    def _verifyDependencies(self, artifact, depth, current = None):
        """
        For each dependency writen in file, read it and get its dependencies
        """
        #if its the first execution for this dependency
        if not current:
            for dependency in self._fileManager.readDependencies(artifact):
                if dependency != 'None':
                    print('Opening dependency:', dependency)
                    self._fileManager.setCurrentArtifact(artifact, 'd', dependency)
                    dep_url = 'https://mvnrepository.com/artifact/' + dependency
                    urlNversion = self._separateV(dep_url, getRoot = True, getVersion = True)
                    dep_root, dep_version = urlNversion[0], urlNversion[1]
                    self._scrap(dep_root,depth,target_version = dep_version)
                    print('Returned to', artifact)
                else: 
                    break
        #if the progress was halted
        else:
            toDo = False
            for dependency in self._fileManager.readDependencies(artifact):
                if dependency != 'None':
                    if dependency == current:
                        toDo = True
                    if toDo:
                        print('Opening dependency:', dependency)
                        self._fileManager.setCurrentArtifact(artifact, 'd', dependency)
                        dep_url = 'https://mvnrepository.com/artifact/' + dependency
                        urlNversion = self._separateV(dep_url, getRoot = True, getVersion = True)
                        dep_root, dep_version = urlNversion[0], urlNversion[1]
                        self._scrap(dep_root,depth,target_version = dep_version)
                        print('Returned to', artifact)
                else:
                    break


    def _verifyUsages(self, artifact, depth, current = None):
        """
        For each usage writen in file, read it and get its usages
        """
        #if its the first execution for this usages
        if not current:
            for usage in self._fileManager.readUsages(artifact):
                if usage != 'None':
                    print('Opening usage:', usage)
                    self._fileManager.setCurrentArtifact(artifact, 'u', usage)
                    self._scrap('https://mvnrepository.com/artifact/' + usage,depth,lookForDependency = artifact)
                    print('Returned to', artifact)
                else:
                    break
        #if progress was halted
        else:
            toDo = False
            for usage in self._fileManager.readUsages(artifact):
                if usage != 'None':
                    if usage == current:
                        toDo = True
                    if toDo:
                        print('Opening usage:', usage)
                        self._fileManager.setCurrentArtifact(artifact, 'u', usage)
                        self._scrap('https://mvnrepository.com/artifact/' + usage,depth,lookForDependency = artifact)
                        print('Returned to', artifact)
                else:
                    break


    def _separateV(self, project, getRoot = False, getVersion = False, getArtifact = False):
        """
        This method receives an url and breaks it in many ways for manipulation
        """
        if project.find('/artifact/') == -1:
            aux1 = project
        else:
            aux1 = project[project.find('/artifact/'):][10:] #return project/artifact/version
        aux2 = aux1[aux1.find('/'):][1:] #return artifact/version
        version = aux2[aux2.find('/'):] #return /version
        root_url = project[:project.find(version)] #return all before /artifact/

        response = []

        if getRoot:
            response.append(root_url)
        if getVersion:
            response.append(version)
        if getArtifact:
            response.append(aux1)

        return response