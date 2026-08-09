import React from "react";

interface Props {

    freshness: any;

}


function FreshnessCard(
    {
        freshness
    }: Props
) {


    return (

        <div>

            <h2>
                Operational Freshness
            </h2>


            <p>
                Last Event:
                {
                    freshness?.last_event
                    ??
                    "None"
                }
            </p>


            <p>
                Time:
                {
                    freshness?.last_event_time
                    ??
                    "Unknown"
                }
            </p>


        </div>

    );

}


export default FreshnessCard;

