const { useState, useEffect } = React;

const formatTime = (timer) => {
    const getSeconds = `0${(timer % 60)}`.slice(-2)
    const minutes = `${Math.floor(timer / 60)}`
    const getMinutes = `0${minutes % 60}`.slice(-2)
    const getHours = `0${Math.floor(timer / 3600)}`.slice(-2)

    return `${getHours} : ${getMinutes} : ${getSeconds}`
}

const StatusEl = ({ state, text }) => {
    return (
        <div>
            <div
                className={`dot0 ${state == 0
                    ? "dot-red"
                    : state == 1
                        ? "dot-green"
                        : state == 2
                            ? "dot-yellow"
                            : ""
                    }`}
            ></div>
            <span>{text}</span>
            <span
                className={`${state == 0
                    ? "text-red"
                    : state == 1 || state == 3
                        ? "text-green"
                        : state == 2
                            ? "text-yellow"
                            : ""
                    }`}
            >
                {" "}
                {state == 0
                    ? "Error"
                    : state == 1
                        ? "Done"
                        : state == 2
                            ? "Progress..."
                            : "-"}{" "}
            </span>
        </div>
    );
};

const NewStatusEl = ({ state, text }) => {
    return (
        <h5>
            <div style={{ display: 'flex', justifyContent: 'start', width: '23rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', width: "160px" }}>
                    <span style={{ justifySelf: 'start' }}>{text}</span>
                    <div>:</div>
                </div>
                <span
                    className={`${state == 0
                        ? "text-red"
                        : state == 1 || state == 3
                            ? "text-green"
                            : state == 2
                                ? "text-yellow"
                                : ""
                        }`}
                    style={{ justifySelf: 'end' }}
                >&nbsp;&nbsp;
                    {state == 0
                        ? " ERROR"
                        : state == 1
                            ? " STARTED"
                            : state == 2
                                ? " PROGRESS....."
                                : state == 3
                                    ? " STOPPED"
                                    : ""}{" "}
                </span>
            </div>
        </h5>
    );
};

function Dot({ state }) {
    return (
        <div
            className={`dot0 ${state == 0
                ? "dot-red"
                : state == 1
                    ? "dot-green"
                    : ""
                }`}
        ></div>
    );
}

function App() {
    // -1 ->idle 0->danger 1->success 2->progress 3->stopped
    const [buttonStates, setButtonStates] = useState({
        dataSync: -1,
        imuOn: -1,
        lidarOn: -1,
        motorOn: -1,
        stopRec: -1,
        startRec: -1,
        motorOff: -1,
        imuOff: -1,
        lidarOff: -1,
        lidarStatus: -1,
        IMUStatus: -1
    });
    const [vel, setVel] = useState(7);
    const [direction, setDirection] = useState(0);
    const [bagsList, setBagsList] = useState([]);
    const [dataType, setDataType] = useState([]);
    const [copying, setCopying] = useState(false);
    const [timer, setTimer] = useState(0)
    const [motorStarted, setMotorStarted] = useState(false);
    const [recordingStarted, setRecordingStarted] = useState(false);
    const countRef = React.useRef(null)

    const resetAllButtonStatus = () => {
        setButtonStates({
            dataSync: -1,
            imuOn: -1,
            lidarOn: -1,
            motorOn: -1,
            stopRec: -1,
            startRec: -1,
            motorOff: -1,
            imuOff: -1,
            lidarOff: -1,
            lidarStatus: -1,
        });
    };


    const resetStopButtonStatuses = () => {
        setButtonStates({
            stopRec: -1,
            motorOff: -1,
            imuOff: -1,
            lidarOff: -1,
        });
    };

    const startTimer = () => {
        setTimer(0)
        countRef.current = setInterval(() => {
            setTimer((timer) => timer + 1)
        }, 1000)
    }

    const stopTimer = () => {
        clearInterval(countRef.current)
    }
    useEffect(() => {
        listLocalRosbags();
    }, []);

    async function initializeLidar() {
        resetAllButtonStatus();

        setButtonStates((prevState) => {
            return { ...prevState, dataSync: 2 };
        });
        const ptpdResponse = await fetch("/ptpd/on", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const ptpdResult = await ptpdResponse.json();
        const rosResponse = await fetch("/roscore/on", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const rosResult = await rosResponse.json();
        if (ptpdResult.success && rosResult.success) {
            setButtonStates((prevState) => {
                return { ...prevState, dataSync: 1 };
            });
        } else {
            setButtonStates((prevState) => {
                return { ...prevState, dataSync: 0 };
            });
            throw Error("datasync issue");
        }

        setButtonStates((prevState) => {
            // return { ...prevState, imuOn: 2 };
            return { ...prevState, IMUStatus: 2 };
        });
        const imuResponse = await fetch("/imu/on", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });

        const imuResult = await imuResponse.json();
        if (!imuResult.success) {
            setButtonStates((prevState) => {
                // return { ...prevState, imuOn: 0 };
                return { ...prevState, IMUStatus: 0 };
            });
        } else {
            // setButtonStates((prevState) => { return { ...prevState, imuOn: 1 } })
        }

        setButtonStates((prevState) => {
            // return { ...prevState, lidarOn: 2 };
            return { ...prevState, lidarStatus: 2 };
        });
        const lidarResponse = await fetch("/lidar/on", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const lidarResult = await lidarResponse.json();
        if (!lidarResult.success) {
            setButtonStates((prevState) => {
                // return { ...prevState, lidarOn: 0 };
                return { ...prevState, lidarStatus: 0 };
            });
        } else {
            // setStatuses(2, "done", lidarResult.msg);
            // checkReadiness(3)
        }

        const statusResponse = await fetch("/topic-statuses", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const statusResult = await statusResponse.json();
        if (statusResult.success) {
            const statusData = statusResult.data;
            setButtonStates((prevState) => {
                return {
                    ...prevState,
                    IMUStatus: statusData[0] ? 1 : 0,
                    lidarStatus: statusData[1] ? 1 : 0,
                };
            });
        } else {
            console.log({ statusResult });
            alert("error");
        }
    }

    async function startMotor() {
        const motorResponse = await fetch(
            `/change-lidar-rot-speed?dir=${direction}&vel=${vel}`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            }
        );
        const motorResult = await motorResponse.json();
        if (!motorResult.success) {
            alert(motorResult.msg)
        } else {
            setMotorStarted(true);
        }
    }

    async function listPendriveRosbags() {
        setDataType("PENDRIVE");
        setBagsList(["loading...."]);
        const rosbagResp = await fetch(`/bags/show-pd`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const rosbagResult = await rosbagResp.json();
        if (!rosbagResult.success) {
            setBagsList(["ERROR"]);
            alert(rosbagResult.msg);
        } else {
            setBagsList(rosbagResult.data);
        }
    }

    async function listLocalRosbags() {
        setDataType("LOCAL");
        setBagsList(["loading...."]);
        const rosbagResp = await fetch(`/bags/show-ld`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const rosbagResult = await rosbagResp.json();
        if (!rosbagResult.success) {
            setBagsList(["ERROR"]);
            alert(rosbagResult.msg);
        } else {
            setBagsList(rosbagResult.data);
        }
    }

    async function copyRosbags() {
        setCopying(true);
        const rosbagResp = await fetch(`/bags/copy`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const rosbagResult = await rosbagResp.json();
        if (!rosbagResult.success) {
            alert(rosbagResult.msg);
        } else {
            listPendriveRosbags();
        }
        setCopying(false);
    }

    async function deletePendriveRosbags() {
        if (!confirm("ARE YOU SURE TO DELETE ALL DATA????")) return;
        setBagsList(["deleting...."]);
        const rosbagResp = await fetch(`/bags/delete-pd`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const rosbagResult = await rosbagResp.json();
        if (!rosbagResult.success) {
            setBagsList(["ERROR"]);
            alert(rosbagResult.msg);
        } else {
            listPendriveRosbags();
        }
    }

    async function deleteLocalRosbags() {
        if (!confirm("ARE YOU SURE TO DELETE ALL DATA????")) return;
        setBagsList(["deleting...."]);
        const rosbagResp = await fetch(`/bags/delete-ld`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const rosbagResult = await rosbagResp.json();
        if (!rosbagResult.success) {
            setBagsList(["ERROR"]);
            alert(rosbagResult.msg);
        } else {
            listLocalRosbags();
        }
    }

    async function mountPendrive() {
        const mountResp = await fetch(`/mount/on`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const mountResult = await mountResp.json();
        if (!mountResult.success) {
            alert(mountResult.msg);
        } else {
            listPendriveRosbags();
        }
    }

    async function unmountPendrive() {
        if (!confirm("ARE YOU SURE TO UNMOUNT THE PENDRIVE????"))
            return;
        setBagsList(["deleting...."]);
        const mountResp = await fetch(`/mount/off`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const mountResult = await mountResp.json();
        if (!mountResult.success) {
            alert(mountResult.msg);
        } else {
            listPendriveRosbags();
        }
    }

    async function stopMotor() {
        const motorResponse = await fetch("/turn-off-lidarmotor", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const motorResult = await motorResponse.json();
        if (!motorResult.success) {
            alert(motorResult.msg)
        } else {
            setMotorStarted(false);
        }
    }

    async function startRecording() {
        const recordResponse = await fetch("/record/on", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const recordResult = await recordResponse.json();
        if (!recordResult.success) {
            console.log(recordResult);
            alert(recordResult.msg);
        } else {
            setRecordingStarted(true)
            startTimer()
        }
    }

    async function stopRecording() {
        stopTimer();
        setButtonStates((prevState) => {
            return { ...prevState, IMUStatus: 2 };
        });
        const imuResponse = await fetch("/imu/off", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const imuResult = await imuResponse.json();
        if (!imuResult.success) {
            setButtonStates((prevState) => {
                return { ...prevState, IMUStatus: 3 };
            });
        } else {
            setButtonStates((prevState) => {
                return { ...prevState, IMUStatus: -1 };
            });
        }

        setButtonStates((prevState) => {
            return { ...prevState, lidarStatus: 3 };
        });
        const lidarResponse = await fetch("/lidar/off", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const lidarResult = await lidarResponse.json();
        if (!lidarResult.success) {
            setButtonStates((prevState) => {
                return { ...prevState, lidarStatus: 0 };
            });
        } else {
            setButtonStates((prevState) => {
                return { ...prevState, lidarStatus: 3 };
            });
        }

        setButtonStates((prevState) => {
            return { ...prevState, stopRec: 2, dataSync: 3 };
        });
        const rosResponse = await fetch("/roscore/off", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const rosResult = await rosResponse.json();

        const recResponse = await fetch("/record/off", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const recResult = await recResponse.json();
        if (!recResult.success) {
        } else {
            setRecordingStarted(false)
        }
    }

    return (
        <div
            style={{
                height: "500px",
                width: "1100px",
                display: "flex",
                gap: "20px",
                padding: "20px",
            }}
        >
            <div
                style={{
                    flex: 2,
                    display: "flex",
                    flexDirection: "column",
                }}
                className="container_left"
            >
                <div
                    style={{
                        flex: 2,
                        color: "white",
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                        flexDirection: "column",
                        gap: "30px",
                        borderBottom: "1px solid grey",
                        padding: '10px'
                    }}
                >
                    <div style={{ width: '34%', marginLeft: '-30%' }}>
                        <NewStatusEl
                            state={buttonStates["dataSync"]}
                            text="Data Syncing"
                        />
                        <NewStatusEl
                            state={buttonStates["lidarStatus"]}
                            text="Lidar Status"
                        />
                        <NewStatusEl
                            state={buttonStates["IMUStatus"]}
                            text="IMU Status"
                        />
                    </div>
                    <div>
                        <button
                            className="btn-style-1"
                            style={{
                                width: "200px",
                                height: "50px",
                            }}
                            onClick={initializeLidar}
                        >
                            Initialize Lidar
                        </button>
                    </div>
                </div>

                <div
                    style={{
                        flex: 1,
                        display: "flex",
                        borderBottom: "1px solid grey",
                    }}
                >
                    <div
                        style={{
                            flex: 1,
                            display: "flex",
                            flexDirection: "column",
                            justifyContent: "center",
                            alignItems: "center",
                            gap: "10px",
                            color: "white",
                            padding: '10px'
                        }}
                    >
                        <span style={{ fontSize: "16px" }}>
                            MOTOR
                        </span>
                        <div style={{ display: 'flex', gap: '20px' }}>
                            <button
                                style={{
                                    border: "none",
                                    background: "transparent",
                                    cursor: motorStarted
                                        ? "default"
                                        : "pointer",
                                }}
                                onClick={motorStarted ? null : startMotor}

                            >
                                <img
                                    src="/static/icons/video-play-green.svg"
                                    alt="play"
                                    width="60px"
                                    style={{
                                        opacity: motorStarted
                                            ? 0.5
                                            : 1,
                                    }}
                                />
                            </button>
                            <button
                                style={{
                                    border: "none",
                                    background: "transparent",
                                    cursor: !motorStarted
                                        ? "default"
                                        : "pointer",
                                }}
                                onClick={motorStarted ? stopMotor : null}
                            >
                                <img
                                    src="/static/icons/stop-button-red.svg"
                                    alt="stop"
                                    width="60px"
                                    style={{
                                        opacity: !motorStarted
                                            ? 0.5
                                            : 1,
                                    }}
                                />
                            </button>
                        </div>
                    </div>
                    <div
                        style={{
                            flex: 1,
                            color: "white",
                            display: "flex",
                            justifyContent: "center",
                            alignItems: "center",
                            flexDirection: "column",
                            gap: "20px",
                            fontSize: "32px",
                            alignItems: "space-between",
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                            <span style={{ fontSize: "16px" }}>
                                Direction:
                            </span>
                            &nbsp;
                            <select
                                name="direction"
                                id="direction"
                                className="btn-style-1"
                                style={{
                                    fontSize: "16px",
                                    padding: "8px",
                                }}
                                onChange={(e) =>
                                    setDirection(
                                        parseInt(e.target.value)
                                    )
                                }
                            >
                                <option
                                    value="0"
                                    style={{ color: "black" }}
                                >
                                    Clockwise
                                </option>
                                <option
                                    value="1"
                                    style={{ color: "black" }}
                                >
                                    Anti-clociwise
                                </option>
                            </select>
                        </div>
                        <div style={{ display: "flex", gap: '20px' }}>
                            <span style={{ fontSize: "16px", marginTop: "7px" }}>
                                Velocity:
                            </span>
                            &nbsp;
                            <div style={{ display: "flex" }}>
                                <button
                                    className="btn-style-1"
                                    style={{
                                        width: "35px",
                                        height: "35px",
                                    }}
                                    onClick={() =>
                                        setVel((prev) => prev > 1 ? prev - 1 : 1)
                                    }
                                >
                                    -
                                </button>
                                <p
                                    className="btn-style-1"
                                    style={{
                                        width: "35px",
                                        height: "35px",
                                        textAlign: "center",
                                        fontSize: "16px",
                                        paddingTop: "6px"
                                    }}
                                >
                                    {vel}
                                </p>
                                <button
                                    className="btn-style-1"
                                    style={{
                                        width: "35px",
                                        height: "35px",
                                    }}
                                    onClick={() =>
                                        setVel((prev) => prev + 1)
                                    }
                                >
                                    +
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <div
                    style={{
                        flex: 1,
                        display: "flex",
                        color: "white",
                    }}
                >
                    <div
                        style={{
                            flex: 1,
                            display: "flex",
                            flexDirection: "column",
                            justifyContent: "center",
                            alignItems: "center",
                            gap: "10px",
                            color: "white",
                            padding: '10px'
                        }}
                    >
                        <span style={{ fontSize: "16px" }}>
                            RECORDING
                        </span>
                        <div style={{ display: 'flex', gap: '20px' }}>
                            <button
                                style={{
                                    border: "none",
                                    background: "transparent",
                                    cursor: recordingStarted
                                        ? "default"
                                        : "pointer",
                                }}
                                onClick={recordingStarted ? null : startRecording}
                            >
                                <img
                                    src="/static/icons/video-play-green.svg"
                                    alt="play"
                                    width="60px"
                                    style={{
                                        opacity: recordingStarted
                                            ? 0.5
                                            : 1,
                                    }}
                                />
                            </button>
                            <button
                                style={{
                                    border: "none",
                                    background: "transparent",
                                    cursor: !recordingStarted
                                        ? "default"
                                        : "pointer",
                                }}
                                onClick={() => recordingStarted && stopRecording()}
                            >
                                <img
                                    src="/static/icons/stop-button-red.svg"
                                    alt="play"
                                    width="60px"
                                    style={{
                                        opacity: !recordingStarted
                                            ? 0.5
                                            : 1,
                                    }}
                                />
                            </button>
                        </div>
                    </div>
                    <div
                        style={{
                            flex: 1,
                            display: "flex",
                            justifyContent: "center",
                            alignItems: "center",
                            fontSize: "35px",
                            fontWight: "bold",
                            display: "flex",
                            gap: "15px",
                        }}
                    >
                        <img
                            src="/static/icons/circle.svg"
                            alt="recording"
                            width="28px"
                            style={{ opacity: 1 }}
                        />{" "}
                        <span>{formatTime(timer)}</span>
                    </div>
                </div>
            </div>
            {/*Data in local*/}
            <div
                className="container_right"
                style={{
                    flex: 1,
                    color: "white",
                }}
            >
                <div
                    style={{
                        borderBottom: "1px solid grey",
                        padding: "10px",
                        display: "flex",
                        justifyContent: "space-between",
                    }}
                >
                    <h4>DATA IN LOCAL</h4>
                    <div>
                        <button
                            style={{
                                border: "none",
                                background: "transparent",
                            }}
                            onClick={listLocalRosbags}
                        >
                            <img
                                src="/static/icons/refresh.svg"
                                alt="refresh"
                                width="18px"
                                style={{ filter: "invert()" }}
                            />
                        </button>
                        &nbsp;
                        <button
                            style={{
                                border: "none",
                                background: "transparent",
                            }}
                            onClick={deleteLocalRosbags}
                        >
                            <img
                                src="/static/icons/delete.svg"
                                alt="clear"
                                width="18px"
                            />
                        </button>
                    </div>
                </div>
                <div style={{ padding: "10px", overflowY: "scroll", height: "86%" }}>
                    <div
                        style={{
                            minHeight: "750px",
                            display: "flex",
                            flexDirection: "column",
                            fontSize: "18px",
                            gap: "5px",
                        }}
                    >
                        {bagsList.length > 0 ? (
                            bagsList.map((bag) => (
                                <div
                                    style={{ paddingLeft: "10px" }}
                                >
                                    {bag}
                                </div>
                            ))
                        ) : (
                            <p align="center">EMPTY</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById("root"));