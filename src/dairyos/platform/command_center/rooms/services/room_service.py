from dairyos.platform.command_center.rooms.models.intelligence_room import (
    IntelligenceRoom,
)



class RoomService:
    """
    Provides operational intelligence rooms.
    """



    def available_rooms(self):

        return [

            IntelligenceRoom(

                name="Herd Room",

                domain="herd",

                status="unknown",

                description="Animal intelligence",

            ),

            IntelligenceRoom(

                name="Milk Room",

                domain="milk",

                status="unknown",

                description="Milk production intelligence",

            ),

            IntelligenceRoom(

                name="Health Room",

                domain="health",

                status="unknown",

                description="Animal health intelligence",

            ),

            IntelligenceRoom(

                name="Feed Room",

                domain="feed",

                status="unknown",

                description="Feed optimization intelligence",

            ),

            IntelligenceRoom(

                name="Finance Room",

                domain="finance",

                status="unknown",

                description="Financial intelligence",

            ),

        ]

