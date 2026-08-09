from dairyos.application.identity.models.user_role import UserRole
from dairyos.application.identity.policies.permission import Permission


ROLE_PERMISSIONS = {

    UserRole.OWNER: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_HERD_STATUS,
        Permission.VIEW_PRODUCTION_STATUS,
        Permission.VIEW_FINANCIAL_STATUS,
        Permission.VIEW_ALERTS,
        Permission.ACKNOWLEDGE_ALERTS,
        Permission.MANAGE_USERS,
    },


    UserRole.FARM_MANAGER: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_HERD_STATUS,
        Permission.VIEW_PRODUCTION_STATUS,
        Permission.RECORD_FEEDING,
        Permission.RECORD_MILK,
        Permission.RECORD_HEALTH_EVENT,
        Permission.RECORD_BREEDING_EVENT,
        Permission.VIEW_ALERTS,
        Permission.ACKNOWLEDGE_ALERTS,
    },


    UserRole.VETERINARIAN: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_HERD_STATUS,
        Permission.VIEW_HEALTH_STATUS,
        Permission.RECORD_HEALTH_EVENT,
        Permission.VIEW_ALERTS,
        Permission.ACKNOWLEDGE_ALERTS,
    },


    UserRole.ACCOUNTANT: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_FINANCIAL_STATUS,
    },


    UserRole.STORE_KEEPER: {
        Permission.VIEW_DASHBOARD,
        Permission.RECORD_FEEDING,
        Permission.VIEW_FEED_TASKS,
    },


    UserRole.MILKING_OPERATOR: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_MILKING_TASKS,
        Permission.RECORD_MILK,
    },


    UserRole.FEED_SUPERVISOR: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_FEED_TASKS,
        Permission.RECORD_FEEDING,
    },


    UserRole.AI_TECHNICIAN: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_HERD_STATUS,
        Permission.RECORD_BREEDING_EVENT,
    },


    UserRole.LABOURER: {
        Permission.VIEW_DASHBOARD,
    },

}
