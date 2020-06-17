class TemplXSCTBuild:
    def __init__(self, sdk_path, version_year, version_number,
                 proc_name='ps7_cortexa9_0', os_name='standalone',
                 hw_name='hw', hw_path=None, sw_name='sw',
                 template_name='Empty Application', create=True,
                 build=True):

        # save version information
        self.version_year = version_year
        self.version_number = version_number

        # initialize text
        self.text = ''

        # apply commands

        self.setws(sdk_path=sdk_path)

        if create:
            self.app_create(
                hw_name=hw_name,
                hw_path=hw_path,
                sw_name=sw_name,
                proc_name=proc_name,
                template_name=template_name,
                os_name=os_name
            )

        if build:
            self.app_build(
                sw_name=sw_name
            )

    def line(self, s='', nl='\n'):
        self.text += f'{s}{nl}'

    def comment(self, s):
        self.line(f'# {s}')

    def setws(self, sdk_path):
        self.comment('set the work directory')
        self.line(f'setws "{sdk_path}"')
        self.line()

    def app_create(self, hw_name, hw_path, sw_name, proc_name,
                   template_name, os_name):
        if self.version_year < 2020:
            self.comment('create the hardware configuration')
            self.line(f'createhw -name {hw_name} -hwspec "{hw_path}"')
            self.line()
            self.comment('create the software configuration')
            self.line(f'createapp -name {sw_name} -hwproject {hw_name} '
                      f'-proc {proc_name} -app "{template_name}"')
            self.line()
        else:
            self.comment('create the app configuration')
            self.line(f'app create -name {sw_name} -hw "{hw_path}" -os {os_name}'
                      f' -proc {proc_name} -template "{template_name}"')
            self.line()

    def app_build(self, sw_name):
        self.comment('build application')
        if self.version_year < 2020:
            self.line('projects -build')
        else:
            self.line(f'app build -name {sw_name}')
        self.line()