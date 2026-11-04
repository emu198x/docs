-- Transparent AY data-port observer. No callback returns replacement data.
local out=assert(os.getenv('PROBE_OUTPUT'))
local cpu=assert(manager.machine.devices[':maincpu'])
local space=assert(cpu.spaces['io'])
local screen=assert(manager.machine.screens[':screen'])
local f=assert(io.open(out..'/ay.tsv','wb'))
assert(f:write('time\tframe\tpc\tcurpc\tregister\tvalue\n'))
local fe=assert(io.open(out..'/fe.tsv','wb'))
assert(fe:write('time\tframe\tpc\tcurpc\tvalue\n'))
local beeper=0
local beeps=0
local selected=0
local count=0
local tap=space:install_write_tap(0,65535,'transparent-ay-command-observer',function(offset,data,mask)
 if (offset&0xc002)==0xc000 then selected=data&15
 elseif (offset&0xc002)==0x8000 then
  count=count+1; assert(count<=100000,'bounded AY log')
  assert(f:write(string.format('%.12f\t%d\t%d\t%d\t%d\t%d\n',emu.time(),screen:frame_number(),cpu.state['PC'].value,cpu.state['CURPC'].value,selected,data)))
 end
 if (offset&1)==0 then
  local level=(data>>4)&1
  if level~=beeper then
   beeper=level; beeps=beeps+1; assert(beeps<=200000,'bounded beeper log')
   assert(fe:write(string.format('%.12f\t%d\t%d\t%d\t%d\n',emu.time(),screen:frame_number(),cpu.state['PC'].value,cpu.state['CURPC'].value,level)))
  end
 end
end)
emu.wait(4.9)
manager.machine.natkeyboard:post_coded('{ENTER}')
emu.wait(210.0-emu.time())
assert(count>0,'no observed AY writes')
assert(f:close()); assert(fe:close()); tap:remove()
local raw,w,h=screen:pixels(); assert(w==352 and h==296 and #raw==352*296*4)
local p=assert(io.open(out..'/final.argb','wb'));assert(p:write(raw));assert(p:close())
print('PROBE_COMPLETE AY '..count)
manager.machine:exit()
