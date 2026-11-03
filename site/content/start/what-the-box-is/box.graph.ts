import { defineGraph } from '$lib/graph/spec';

// The box as it is decided: the hardware, the processes on the Pi, and what flows between them.
// Hardware is on the left and along the bottom, the Pi's host processes in the middle, and the ROS
// nodes in the Pixi environment on the right.

export const box = defineGraph({
    title: 'The box',
    caption:
        'TIMEPULSE disciplines the Pi’s clock through chrony and locks the Pico’s camera triggers. ' +
        'ubx_mux owns the receiver’s USB port, so time sync runs without ROS, and forwards the UBX ' +
        'stream to the ROS driver. How trigger times reach trigger_bridge is not decided yet. ' +
        'Power comes from one USB-C input to the Pi; the AD3 probes the timing lines on the bench.',
    width: 900,
    height: 560,
    nodeRadius: 50,
    fontSize: 14,
    nodeKinds: {
        hardware: { name: 'Hardware', hue: 'gray', shape: 'square' },
        host: { name: 'Host process on the Pi, outside ROS', hue: 'blue', shape: 'square' },
        ros: { name: 'ROS 2 node, in the Pixi environment', hue: 'green', shape: 'square' },
    },
    edgeKinds: {
        timing: { name: 'Timing: PPS and trigger', hue: 'red' },
        data: { name: 'Data' },
        undecided: { name: 'Not decided yet', hue: 'amber', line: 'dashed' },
    },
    nodes: [
        { id: 'f9r', x: 110, y: 420, kind: 'hardware', label: 'ZED-F9R' },
        { id: 'logger', x: 110, y: 130, kind: 'hardware', label: 'SD logger' },
        { id: 'pico', x: 330, y: 90, kind: 'hardware', label: 'Pico' },
        { id: 'camera', x: 560, y: 90, kind: 'hardware', label: 'IMX296' },
        { id: 'mux', x: 330, y: 470, kind: 'host', label: 'ubx_mux' },
        { id: 'chrony', x: 330, y: 290, kind: 'host', label: 'chrony' },
        { id: 'driver', x: 560, y: 470, kind: 'ros', label: 'ubx_driver' },
        { id: 'cam', x: 560, y: 270, kind: 'ros', label: 'camera_ros' },
        { id: 'bridge', x: 790, y: 160, r: 60, kind: 'ros', label: 'trigger_bridge' },
        { id: 'rec', x: 790, y: 400, kind: 'ros', label: 'recorder' },
    ],
    edges: [
        { from: 'f9r', to: 'mux', kind: 'data', label: 'UBX, USB' },
        { from: 'f9r', to: 'chrony', kind: 'timing', label: 'PPS' },
        { from: 'f9r', to: 'pico', kind: 'timing', label: 'PPS', labelAt: 0.35 },
        { from: 'f9r', to: 'logger', kind: 'data', label: 'raw UBX, UART' },
        { from: 'mux', to: 'chrony', kind: 'data', label: 'coarse time' },
        { from: 'mux', to: 'driver', kind: 'data' },
        { from: 'pico', to: 'camera', kind: 'timing', label: 'trigger' },
        { from: 'camera', to: 'cam', kind: 'data', label: 'CSI' },
        { from: 'cam', to: 'bridge', kind: 'data' },
        {
            from: 'pico',
            to: 'bridge',
            kind: 'undecided',
            via: [[560, 20]],
            label: 'trigger times',
            labelAt: 0.8,
        },
        { from: 'driver', to: 'rec', kind: 'data' },
        { from: 'cam', to: 'rec', kind: 'data' },
        { from: 'bridge', to: 'rec', kind: 'data' },
    ],
});
