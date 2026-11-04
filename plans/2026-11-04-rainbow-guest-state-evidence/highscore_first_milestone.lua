-- Observe the original program's first BEST 5 page-complete delay entry.
local out=assert(os.getenv("PROBE_OUTPUT"))
local screen=assert(manager.machine.screens[":screen"])
local cpu=assert(manager.machine.devices[":maincpu"])
local space=assert(cpu.spaces["program"])
local ram=emu.item(assert(manager.machine.devices[":ram"].items["0/m_pointer"]))
local page7=emu.item(assert(manager.machine.devices[":"].items["0/m_port_7ffd_data"]))
local page1=emu.item(assert(manager.machine.devices[":"].items["0/m_port_1ffd_data"]))
assert(ram.size==1 and ram.count==131072)
local function write(name,data)
 local f=assert(io.open(out.."/"..name,"wb")); assert(f:write(data)); assert(f:close())
end
local function reg(name) return assert(cpu.state[name]).value end
local function word(address)
 assert(address>=0xc000)
 local bank=page7:read(0)&7
 local offset=bank*16384+(address&16383)
 return ram:read(offset) | (ram:read(offset+1)<<8)
end
local event=nil
local matches=0
local tap=space:install_read_tap(0xcfc9,0xcfc9,"rainbow-best5-page-complete",function(offset,data,mask)
 if not event and reg("SP")==0xfffa and (page1:read(0)&1)==0
   and word(0xfffa)==0xd000 and word(0xfffc)==0xcfad then
  assert(data==0x01,"unexpected original program opcode")
  matches=matches+1
  event=string.format("frame=%d\ntime=%.12f\npc=%d\ncurpc=%d\nsp=%d\nsaved_bc=%d\nreturn_pc=%d\n",screen:frame_number(),emu.time(),reg("PC"),reg("CURPC"),reg("SP"),word(0xfffa),word(0xfffc))
  write("milestone.ram",ram:read_block(0,131072))
  write("milestone.toml",event)
 end
end)
emu.wait(4.9)
manager.machine.natkeyboard:post_coded("{ENTER}")
local waited=0
while not event do
 assert(waited<6000,"BEST 5 page-complete milestone not reached")
 emu.wait(screen.frame_period); waited=waited+1
end
assert(matches==1)
emu.wait(2*screen.frame_period)
local first=screen:frame_number()
for i=0,63 do
 if i>0 then emu.wait(screen.frame_period) end
 assert(screen:frame_number()==first+i,"native field mismatch")
 local raw=ram:read_block(0,131072)
 write(string.format("%03d.ram",i),raw)
 local pixels,w,h=screen:pixels(); assert(w==352 and h==296 and #pixels==352*296*4)
 write(string.format("%03d.argb",i),pixels)
 if i==0 then assert(screen:snapshot(out.."/highscore.png")==nil) end
 print("NATIVE_FIELD "..i.." "..screen:frame_number())
end
assert(emu.time()<125.35,"first-page observation overran control checkpoint")
emu.wait(125.35-emu.time())
write("checkpoint.ram",ram:read_block(0,131072))
local pixels,w,h=screen:pixels(); assert(w==352 and h==296)
write("checkpoint.argb",pixels)
assert(tap); tap:remove()
print("PROBE_COMPLETE highscore-milestone 64")
manager.machine:exit()
