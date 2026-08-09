from ..models.equipment_asset import EquipmentAsset



class EquipmentManagementService:



    def evaluate(

        self,

        equipment_id,

        equipment_name,

        category,

        condition

    ):


        if condition.lower() == "good":

            operational_status = "OPERATIONAL"

            maintenance_priority = "NORMAL"

            action = "Continue scheduled maintenance"



        elif condition.lower() == "fair":

            operational_status = "OPERATIONAL"

            maintenance_priority = "MONITOR"

            action = "Schedule inspection"



        else:

            operational_status = "ATTENTION"

            maintenance_priority = "HIGH"

            action = "Immediate maintenance required"



        return EquipmentAsset(

            equipment_id,

            equipment_name,

            category,

            operational_status,

            maintenance_priority,

            action

        )
