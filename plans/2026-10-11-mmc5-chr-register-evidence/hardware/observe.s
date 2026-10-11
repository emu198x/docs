; MMC5 CHR observation, not a pass/fail oracle for unknown latch inputs.
; Rendering stays disabled during all mapper observations.
.setcpu "6502"
.segment "CODE"

.macro ppu_address address
    bit $2002
    lda #>(address)
    sta $2006
    lda #<(address)
    sta $2006
.endmacro

.macro message address, label
    ppu_address address
    ldx #0
:
    lda label,x
    beq :+
    sta $2007
    inx
    bne :-
:
.endmacro

.macro matrix address, source
    .repeat 4, row
        ppu_address address + row * 32
        lda #'0' + row
        sta $2007
        lda #':'
        sta $2007
        lda #' '
        sta $2007
        ldx #0
    :
        lda source + row * 8,x
        jsr hex_byte
        lda #' '
        sta $2007
        inx
        cpx #8
        bne :-
    .endrepeat
.endmacro

reset:
    sei
    cld
    ldx #$FF
    txs
    lda #0
    sta $2000
    sta $2001
    sta $4010
    sta $4015
    sta $04F0
    sta $04F1
    sta $04F2
    lda #$40
    sta $4017
    bit $2002
wait_first:
    bit $2002
    bpl wait_first
wait_second:
    bit $2002
    bpl wait_second

    lda #3
    sta $5100
    lda #$FF
    sta $5117
    lda #0
    sta $5104
    sta $5105                 ; all nametables use CIRAM page 0
    sta $5130
    sta $5200                 ; disable split and mapper IRQ
    sta $5204
    ldx #0
sample:
    txa
    lsr
    lsr
    lsr
    sta $5101                 ; write-time mode 0, 1, 2, or 3
    txa
    and #7
    sta $5127
    jsr sample_address
    lda $2007                 ; buffered read after dummy in subroutine
    sta $0420,x               ; unchanged-mode control
    lda #3
    sta $5101                 ; expose retained bits in 1 KiB mode
    jsr sample_address
    lda $2007
    sta $0400,x               ; retained page number
    lda $2007
    sta $0440,x               ; next byte must be its complement
    eor $0400,x
    cmp #$FF
    beq complement_ok
    inc $04F2
complement_ok:
    jsr sample_address
    lda $2007
    sta $0460,x               ; independent repeated buffered read
    cmp $0400,x
    beq repeat_ok
    inc $04F2
repeat_ok:
    inx
    cpx #32
    bne sample
    stx $04F7                 ; nonzero completed-row count
    lda #$A5
    sta $04F0                 ; samples complete; display not ready yet
    lda #'M'
    sta $04F3
    lda #'5'
    sta $04F4
    lda #'C'
    sta $04F5
    lda #'1'
    sta $04F6

    ; Display uses ordinary 1 KiB banking, after all observations are saved.
    ldx #0
font_banks:
    txa
    sta $5120,x
    inx
    cpx #8
    bne font_banks
    ppu_address $2000
    ldx #4
    ldy #0
    lda #' '
clear_page:
    sta $2007
    iny
    bne clear_page
    dex
    bne clear_page
    ppu_address $23C0
    ldx #64
    lda #0
clear_attributes:
    sta $2007
    dex
    bne clear_attributes
    ppu_address $3F00
    ldx #0
palette:
    lda colours,x
    sta $2007
    inx
    cpx #32
    bne palette

    message $2043, title
    message $2082, inputs
    message $20A3, retained_label
    matrix $20C2, $0400
    message $2163, static_label
    matrix $2182, $0420
    message $2243, checks_label
    lda $04F2
    jsr hex_byte
    message $2283, footer

    bit $2002
    lda #0
    sta $2005
    sta $2005
    sta $2000
    lda #$0A
    sta $2001
    lda #$A5
    sta $04F1                 ; display ready
forever:
    jmp forever

sample_address:
    ppu_address $1C00         ; $5127 selects this address in every mode
    lda $2007                 ; discard old PPU read buffer
    rts

hex_byte:
    pha
    lsr
    lsr
    lsr
    lsr
    tay
    lda digits,y
    sta $2007
    pla
    and #15
    tay
    lda digits,y
    sta $2007
    rts

interrupt:
    rti
digits: .byte "0123456789ABCDEF"
title: .byte "MMC5 CHR OBSERVATION",0
inputs: .byte "IN 00 01 02 03 04 05 06 07",0
retained_label: .byte "MODE THEN 1K WITHOUT WRITE",0
static_label: .byte "MODE WITHOUT CHANGE",0
checks_label: .byte "READ CHECK ERRORS ",0
footer: .byte "DONE - RECORD CHIP / BOARD",0
colours:
    .repeat 8
        .byte $0F,$30,$10,$00
    .endrepeat

.segment "VECTORS"
    .word interrupt, reset, interrupt
