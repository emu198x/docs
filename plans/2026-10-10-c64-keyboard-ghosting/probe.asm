; CIA1 pin reads with host-held keys; no KERNAL keyboard scan.
*=$0801
!byte $0b,$08,$0a,0,$9e
!text "2064"
!byte 0,0,0
*=$0810
 sei
 lda #$7f
 sta $dc0d
 sta $dd0d
 lda $dc0d
 lda $dd0d
 lda #$35
 sta $01
 lda #0
 sta $dc02
 sta $dc03
 sta $dc0e
 sta $dc0f
ready:
 lda request
 beq ready
 lda config
 sta $dc00
 lda config+1
 sta $dc01
 lda config+2
 sta $dc02
 lda config+3
 sta $dc03
 lda $dc00
 and config+4
 sta observed
 lda $dc01
 and config+4
 sta observed+1
done:
 jmp done
request: !byte 0
config: !byte $ff,$ff,0,0,$ff
observed: !fill 2,0
