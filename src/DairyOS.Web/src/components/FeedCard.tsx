import React from "react";

interface Props {

    feed: any;

}


function FeedCard(
    {
        feed
    }: Props
) {


    return (

        <div>

            <h2>
                Feeding
            </h2>


            <p>
                Today:
                {
                    feed?.today_kg
                    ??
                    "No data"
                }
                kg
            </p>


            <p>
                Events:
                {
                    feed?.events
                    ??
                    0
                }
            </p>


            <p>
                Type:
                {
                    feed?.last_feed_type
                    ??
                    "Unknown"
                }
            </p>


        </div>

    );

}


export default FeedCard;

