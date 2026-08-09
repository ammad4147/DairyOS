import React from "react";

interface Props {

    decisions: any[];

}


function AttentionPanel(
    {
        decisions
    }: Props
) {


    return (

        <div>

            <h2>
                Attention Required
            </h2>


            {
                decisions.length === 0

                ?

                <p>
                    No pending attention items
                </p>

                :

                decisions.map(
                    (
                        decision,
                        index
                    ) => (

                        <div key={index}>

                            <strong>
                                {
                                    decision
                                    .priority
                                }
                            </strong>

                            <p>
                                {
                                    decision
                                    .title
                                }
                            </p>


                        </div>

                    )
                )

            }


        </div>

    );

}


export default AttentionPanel;

