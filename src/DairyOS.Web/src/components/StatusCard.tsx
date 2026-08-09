import React from "react";

interface Props {

    title: string;

    value: string | number;

}


function StatusCard(
    {
        title,
        value
    }: Props
) {

    return (

        <div>

            <h3>
                {title}
            </h3>

            <p>
                {value}
            </p>

        </div>

    );

}


export default StatusCard;

