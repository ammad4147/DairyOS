from dairyos.farm.herd.models.animal_operational_state import (
    AnimalOperationalState,
)

from dairyos.operations.commands.models.operational_command import (
    OperationalCommand,
)


class AnimalCommandGenerationService:
    """
    Converts animal operational conditions
    into executable operational commands.

    Flow:

    AnimalOperationalState
            |
            v
    OperationalCommand

    Does not:
    - execute commands
    - mutate animal state
    - bypass decisions
    """



    def generate(
        self,
        state: AnimalOperationalState,
    ) -> list[OperationalCommand]:

        commands = []


        if state.attention_required:

            commands.extend(
                self._generate_attention_commands(
                    state
                )
            )


        if state.intelligence_attention_required:

            commands.extend(
                self._generate_intelligence_commands(
                    state
                )
            )


        return commands



    def _generate_attention_commands(
        self,
        state,
    ):

        commands = []


        for reason in state.attention_reason:

            commands.append(

                OperationalCommand(

                    command_type="animal_health_review",

                    actor="SYSTEM",

                    payload={

                        "animal_id":
                            state.animal_id,

                        "reason":
                            reason,

                        "source":
                            "AnimalOperationalState",

                    },

                )

            )


        return commands



    def _generate_intelligence_commands(
        self,
        state,
    ):

        commands = []


        for reason in state.intelligence_attention_reason:

            commands.append(

                OperationalCommand(

                    command_type="animal_operational_review",

                    actor="SYSTEM",

                    payload={

                        "animal_id":
                            state.animal_id,

                        "reason":
                            reason,

                        "source":
                            "AnimalIntelligence",

                    },

                )

            )


        return commands
