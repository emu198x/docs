-- Transparent AY data-port observer. No callback returns replacement data.
local out=assert(os.getenv('PROBE_OUTPUT'))
local cpu=assert(manager.machine.devices[':maincpu'])
local space=assert(cpu.spaces['io'])
local screen=assert(manager.machine.screens[':screen'])
local f=assert(io.open(out..'/ay.tsv','wb'))
assert(f:write('time\tframe\tpc\tcurpc\tregister\tvalue\n'))
local selected=0
local count=0
local tap=space:install_write_tap(0,65535,'transparent-ay-command-observer',function(offset,data,mask)
 if (offset&0xc002)==0xc000 then selected=data&15
 elseif (offset&0xc002)==0x8000 then
  count=count+1; assert(count<=150000,'bounded AY log')
  assert(f:write(string.format('%.12f\t%d\t%d\t%d\t%d\t%d\n',emu.time(),screen:frame_number(),cpu.state['PC'].value,cpu.state['CURPC'].value,selected,data)))
 end
end)
emu.wait(4.9)
manager.machine.natkeyboard:post_coded('{ENTER}')
emu.wait(210.0-emu.time())
assert(count>0,'no observed AY writes')
assert(f:close()); tap:remove()
local ram=emu.item(assert(manager.machine.devices[':ram'].items['0/m_pointer']))
assert(ram.count==131072 and ram.size==1)
local root=manager.machine.devices[':']
local page7=emu.item(assert(root.items['0/m_port_7ffd_data']))
local page1=emu.item(assert(root.items['0/m_port_1ffd_data']))
local info=assert(io.open(out..'/state.tsv','wb'))
assert(info:write('frame\tpc\tsp\tpage7\tpage1\n'))
for i=0,63 do
 if i>0 then emu.wait(screen.frame_period) end
 local raw,w,h=screen:pixels(); assert(w==352 and h==296 and #raw==352*296*4)
 local f=assert(io.open(out..string.format('/%03d.argb',i),'wb'));assert(f:write(raw));assert(f:close())
 local f=assert(io.open(out..string.format('/%03d.ram',i),'wb'));assert(f:write(ram:read_block(0,131072)));assert(f:close())
 assert(info:write(string.format('%d\t%d\t%d\t%d\t%d\n',screen:frame_number(),cpu.state['PC'].value,cpu.state['SP'].value,page7:read(0),page1:read(0))))
end
assert(info:close())
local raw,w,h=screen:pixels(); assert(w==352 and h==296 and #raw==352*296*4)
local p=assert(io.open(out..'/final.argb','wb'));assert(p:write(raw));assert(p:close())
print('PROBE_COMPLETE AY '..count)
manager.machine:exit()
