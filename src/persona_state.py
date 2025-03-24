import json
from pprint import pprint

class PersonaStateManager:
    def __init__(self, persona_config, db, session):
        self.state_obj_dict = {}
        self.db = db
        self.session = session
        self.current_state = self.db.states.get_persona_current_state(session.user_id, session.agent_id)
        if self.current_state == None:
            self.current_state = persona_config['framework_settings']['state_settings']['starting_state']
            self.db.states.set_persona_current_state(self.session.user_id, self.session.agent_id, self.current_state)
        for state_name, state_config in persona_config['states'].items():
            self.state_obj_dict[state_name] = PersonaState(self, state_name, state_config, self.db)

    def get_state_obj(self, state_name=None):
        if state_name:
            return self.state_obj_dict[state_name]
        return self.state_obj_dict[self.current_state]

    def update_state_from_llm_response(self, llm_response):
        state_obj = self.get_state_obj()
        state_obj.update_state_from_llm_response(llm_response)

    def set_current_state(self, state_name):
        if state_name not in self.state_obj_dict.keys():
            breakpoint()
        self.current_state = state_name
        self.db.states.set_persona_current_state(self.session.user_id, self.session.agent_id, state_name)


class PersonaState:

    def __init__(self, state_manager, state_name, state_config, db):
        self.state_manager = state_manager
        self.name = state_name
        self.db = db
        self.config = state_config
        self.data_schema = {
            'goals': {}
        }
        for (goal_name, goal_config) in state_config['goals'].items():
            self.data_schema['goals'][goal_name] = {
                'data': goal_config['data']
            }

        #self.data_schema = state_config['data']
        self.data = self.db.states.get_persona_state_data(self.state_manager.session.user_id, self.state_manager.session.agent_id, state_name)

    @property
    def data_schema_json(self):
        return json.dumps(self.data_schema)

    # This method will update the state's data object with the data from the LLM response
    def update_state_from_llm_response(self, llm_response):
        if self.data == None:
            new_data = {'goals': {}}
            for goal_name, goal_config in llm_response['data']['goals'].items():
                if goal_name not in self.data_schema['goals']:
                    breakpoint()
                for key, value in goal_config['data'].items():
                    if key not in self.data_schema['goals'][goal_name]['data'].keys():
                        breakpoint()
                new_data['goals'][goal_name] = {
                    'data': goal_config['data']
                }
            self.data = new_data
        else:
            # Update self.data dict with the new data from the LLM response
            # It will verify that the keys are in the data schema and that no new keys exist
            for goal_name, goal_config in llm_response['data']['goals'].items():
                if goal_name not in self.data_schema['goals']:
                    breakpoint()
                for key, value in goal_config['data'].items():
                    if key not in self.data_schema['goals'][goal_name]['data'].keys():
                        breakpoint()
                    if value != None:
                        self.data['goals'][goal_name]['data'][key] = value

        self.db.states.set_persona_state_data(self.state_manager.session.user_id, self.state_manager.session.agent_id, self.name, self.data)

        # Change the state if necessary
        self.state_manager.set_current_state(llm_response['next_state'])


