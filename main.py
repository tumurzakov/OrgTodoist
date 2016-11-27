import os, sys, inspect

cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
sys.path.append(os.path.join(cmd_folder))
sys.path.append(os.path.join(cmd_folder, "./dist/PyOrgMode"))
sys.path.append(os.path.join(cmd_folder, "./dist/todoist-python"))

from PyOrgMode import PyOrgMode
import todoist
import os.path
import locale
import dateutil.parser
import config

from datetime import datetime
from dateutil import tz

class OrgTodoist:
    def __init__(self):
        self.token = config.TODOIST_TOKEN
        self.org_file = config.TODOIST_FILE;

        self.api = todoist.TodoistAPI(token=self.token)

        self.__touch_org_file()
        self.org = PyOrgMode.OrgDataStructure()
        self.org.load_from_file(self.org_file)

        self.changed = 0

    def __touch_org_file(self):
        try:
            if not os.path.isfile(self.org_file):
                open(self.org_file, 'a').close()
        except:
            pass

    def read_todos(self):
        self.todos = []
        for node in self.org.root.content:
            todo = {'node': node}
            for content in node.content:
                if isinstance(content, basestring):
                    pass

                elif content.TYPE == 'SCHEDULE_ELEMENT':
                    if content.type == 2:
                        todo['SCHEDULED'] = content

                elif content.TYPE == 'DRAWER_ELEMENT':
                    todo['PROPERTIES'] = content.content
                    for prop in content.content:
                        todo[prop.name] = prop.value

            self.todos.append(todo)

    def sync_todoist(self):
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

        self.api.sync_token='*'
        response = self.api.sync()
        self.todoist_items = response['items']

    def __process_scheduled(self, todo, item):
        _due = datetime.today()
        if item['due_date_utc']:
            _due = self.__get_localtime(item['due_date_utc'])
        _sched = PyOrgMode.OrgSchedule()

        if 'SCHEDULED' in todo and todo['SCHEDULED']:
            scheduled = todo['SCHEDULED'].scheduled.get_value()
            if scheduled[1:11] != _due.strftime("%F"):
                todo['SCHEDULED'].scheduled = PyOrgMode.OrgDate("<%s>" % _due.strftime("%F"))
                self.changed = 1
        else:
            _sched._append(todo['node'], _sched.Element(scheduled="<%s>" % _due.strftime("%F")))
            self.changed = 1

    def __process_props(self, todo, item):
        if 'PROPERTIES' in todo:
            todo['PROPERTIES'].append(PyOrgMode.OrgDrawer.Property("TODOIST_ID", "%d" % item['id']))
        else:
            _props = PyOrgMode.OrgDrawer.Element("PROPERTIES")
            _props.append(PyOrgMode.OrgDrawer.Property("TODOIST_ID", "%d" % item['id']))
            todo['node'].append_clean(_props)

        self.changed = 1

    def bind(self):
        item_ids = []
        for item in self.todoist_items:
            found = 0
            for todo in self.todos:
                if 'TODOIST_ID' in todo and int(todo['TODOIST_ID']) == item['id']:
                    item_ids.append(todo['TODOIST_ID'])
                    heading = item['content'].encode('utf-8').strip()
                    if todo['node'].heading != heading:
                        todo['node'].heading = heading
                        self.changed = 1

                    self.__process_scheduled(todo, item)

                    found = 1

            if not found:
                new_todo = PyOrgMode.OrgNode.Element()
                new_todo.heading = item['content'].encode('utf-8').strip()
                new_todo.todo = "TODO"

                self.__process_props({'node':new_todo}, item)
                self.__process_scheduled({'node':new_todo}, item)

                self.org.root.append_clean(new_todo)

                self.changed = 1

        for todo in self.todos:
            if 'TODOIST_ID' in todo and todo['node'].todo == 'DONE' and todo['TODOIST_ID'] in item_ids:
                item = self.api.items.get_by_id(int(todo['TODOIST_ID']))
                item.complete()
                self.api.commit()

    def __get_localtime(self, date):
        utc_zone = tz.tzutc()
        loc_zone = tz.tzlocal()

        utc = dateutil.parser.parse(date).replace(tzinfo=utc_zone)

        return utc.astimezone(loc_zone)


    def save(self):
        if self.changed:
            self.org.save_to_file(self.org_file)

def main():
    orgTodoist = OrgTodoist()
    orgTodoist.read_todos()
    orgTodoist.sync_todoist()
    orgTodoist.bind()
    orgTodoist.save()

if __name__ == "__main__":
    main()
