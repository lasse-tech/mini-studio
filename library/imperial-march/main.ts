// Imperial March main theme (trumpet line, bars 6-17 of the orchestral MIDI).
// Button A plays it; until then the LEDs show the program is ready.
// The built-in speaker is available on the Calliope mini V3.
const sixteenth = 147 // ms at 102 bpm
// Pairs of frequency in Hz (0 = rest) and length in sixteenths, one line per bar
const melody = [
    392, 4, 392, 4, 392, 4, 311, 3, 466, 1,
    392, 4, 311, 3, 466, 1, 392, 8,
    587, 4, 587, 4, 587, 4, 622, 3, 466, 1,
    370, 4, 311, 3, 466, 1, 392, 8,
    784, 4, 392, 3, 392, 1, 784, 4, 740, 3, 698, 1,
    659, 1, 622, 1, 659, 2, 0, 2, 415, 2, 554, 4, 523, 3, 494, 1,
    466, 1, 440, 1, 466, 2, 0, 2, 311, 2, 370, 4, 311, 3, 370, 1,
    466, 4, 392, 3, 466, 1, 587, 8,
    784, 4, 392, 3, 392, 1, 784, 4, 740, 3, 698, 1,
    659, 1, 622, 1, 659, 2, 0, 2, 415, 2, 554, 4, 523, 3, 494, 1,
    466, 1, 440, 1, 466, 2, 0, 2, 311, 2, 370, 4, 311, 3, 466, 1,
    392, 4, 311, 3, 466, 1, 392, 8,
]

function playMarch() {
    for (let i = 0; i < melody.length; i += 2) {
        const frequency = melody[i]
        const length = melody[i + 1] * sixteenth
        if (frequency == 0) {
            basic.clearScreen()
            music.rest(length)
            continue
        }
        // Interval 0: showLeds pauses 400 ms by default
        if (i % 4 == 0) {
            basic.showLeds(`
                # . . . #
                . # . # .
                . . # . .
                . # . # .
                # . . . #
            `, 0)
        } else {
            basic.showLeds(`
                . . # . .
                . # # # .
                # # # # #
                . # # # .
                . . # . .
            `, 0)
        }
        const sound = Math.idiv(length * 85, 100)
        music.playTone(frequency, sound)
        basic.clearScreen()
        music.rest(length - sound)
    }
}

function showReady() {
    basic.showLeds(`
        # . . . #
        . # . # .
        . . # . .
        . # . # .
        # . . . #
    `, 0)
}

input.onButtonPressed(Button.A, function () {
    playMarch()
    showReady()
})

showReady()
