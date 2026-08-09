import React from "react";

interface Props {

    animals: any;

    widgets?: Array<{
        widget_id: string;
        title: string;
        value: string | number | null;
    }>;

}


function HerdCard(
    {
        animals,
        widgets = []
    }: Props
) {


    return (

        <div>

            <h2>
                Herd Status
            </h2>


            <p>
                Total:
                {
                    animals?.total
                    ??
                    0
                }
            </p>


            <p>
                Milking:
                {
                    animals?.milking
                    ??
                    0
                }
            </p>


            <p>
                Dry:
                {
                    animals?.dry
                    ??
                    0
                }
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


        </div>

    );

}


export default HerdCard;

