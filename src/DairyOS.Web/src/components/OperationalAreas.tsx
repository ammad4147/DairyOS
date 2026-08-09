import React from "react";

interface Props {

    state: any;

}


function OperationalAreas(
    {
        state
    }: Props
) {


    const areas = [

        "milk_status",

        "feeding_status",

        "health_status",

        "breeding_status",

        "workforce_status",

        "inventory_status",

        "equipment_status",

        "financial_status",

    ];



    return (

        <div>

            <h2>
                Operational Areas
            </h2>


            {
                areas.map(

                    area => (

                        <div key={area}>

                            <strong>
                                {
                                    area
                                }
                            </strong>


                            <p>

                                {
                                    state[area]
                                    ?

                                    JSON.stringify(
                                        state[area]
                                    )

                                    :

                                    "No data"

                                }

                            </p>


                        </div>

                    )

                )
            }


        </div>

    );

}


export default OperationalAreas;

