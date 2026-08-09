from dataclasses import dataclass


@dataclass
class MilkHealthSignal:

    signal_type: str

    severity: str

    source: str = "MILK_INTELLIGENCE"



class MilkHealthBridgeService:


    def create_signal(
        self,
        anomaly
    ):


        if not anomaly:

            return None


        severity = anomaly.get(
            "severity",
            "MEDIUM"
        )


        return MilkHealthSignal(

            signal_type="MILK_YIELD_DROP",

            severity=severity

        )



    def create_signals(
        self,
        anomalies
    ):


        signals = []


        for anomaly in anomalies:

            signal = self.create_signal(
                anomaly
            )


            if signal:

                signals.append(
                    signal
                )


        return signals



    def assess_milk_event(
        self,
        animal_id,
        anomaly,
        health_service
    ):


        signal = self.create_signal(
            anomaly
        )


        if not signal:

            return None



        return health_service.assess(

            animal_id,

            [

                signal

            ]

        )
