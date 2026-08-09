import React from "react";

interface Props {

    milk: any;

    widgets?: Array<{
        widget_id: string;
        title: string;
        value: string | number | null;
    }>;

}


function ProductionCard(
    {
        milk,
        widgets = []
    }: Props
) {

    return (

        <div>

            <h2>
                Milk Production
            </h2>


            <p>
                Today:
                {
                    milk?.today_litres
                    ??
                    "No data"
                }
                litres
            </p>

            {
                widgets.map(
                    widget => (
                        <p key={widget.widget_id}>
                            {widget.title}: {widget.value ?? "No data"}
                        </p>
                    )
                )
            }


            <p>
                Events:
                {
                    milk?.events
                    ??
                    0
                }
            </p>


            <p>
                Operator:
                {
                    milk?.last_operator
                    ??
                    "Unknown"
                }
            </p>


        </div>

    );

}


export default ProductionCard;

