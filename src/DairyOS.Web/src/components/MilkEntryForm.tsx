import React, {
    useState,
} from "react";

import {
    recordMilkEntry,
} from "../api/farmEntryClient";



function MilkEntryForm() {


    const [animalId, setAnimalId] =
        useState("");

    const [morning, setMorning] =
        useState(0);

    const [afternoon, setAfternoon] =
        useState(0);

    const [evening, setEvening] =
        useState(0);


    const [message, setMessage] =
        useState("");



    async function submitEntry() {

        try {

            const result =
                await recordMilkEntry(
                    {

                        animal_id:
                            animalId,

                        morning_yield:
                            morning,

                        afternoon_yield:
                            afternoon,

                        evening_yield:
                            evening,

                    }
                );


            setMessage(
                `Milk recorded: ${result.total_yield} litres`
            );


        }
        catch (error) {

            setMessage(
                "Milk entry failed"
            );

        }

    }



    return (

        <div>

            <h2>
                Milk Production Entry
            </h2>


            <div>

                <label>
                    Animal ID
                </label>

                <input

                    value={animalId}

                    onChange={
                        e =>
                        setAnimalId(
                            e.target.value
                        )
                    }

                />

            </div>



            <div>

                <label>
                    Morning Yield
                </label>

                <input

                    type="number"

                    value={morning}

                    onChange={
                        e =>
                        setMorning(
                            Number(
                                e.target.value
                            )
                        )
                    }

                />

            </div>



            <div>

                <label>
                    Afternoon Yield
                </label>

                <input

                    type="number"

                    value={afternoon}

                    onChange={
                        e =>
                        setAfternoon(
                            Number(
                                e.target.value
                            )
                        )
                    }

                />

            </div>



            <div>

                <label>
                    Evening Yield
                </label>

                <input

                    type="number"

                    value={evening}

                    onChange={
                        e =>
                        setEvening(
                            Number(
                                e.target.value
                            )
                        )
                    }

                />

            </div>



            <button
                onClick={
                    submitEntry
                }
            >

                Record Milk

            </button>



            <p>

                {message}

            </p>


        </div>

    );

}


export default MilkEntryForm;
