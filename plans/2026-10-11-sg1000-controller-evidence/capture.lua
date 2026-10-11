local output = assert(io.open('/private/tmp/198x-sg1000-input-evidence/mame.csv','w'))
output:write('state,p1,p2,even,odd,before,after\n')
local machine = manager.machine
local ram = assert(machine.devices[':z80']).spaces['program']
local p1 = assert(machine.ioport.ports[':ctrl1:mspad:JOYPAD'])
local p2 = assert(machine.ioport.ports[':ctrl2:mspad:JOYPAD'])
local state, phase, before = 0, 0, 0
local failed = false
local function step()
 if phase == 0 then
  for bit=0,5 do
   assert(p1:field(1 << bit)):set_value((state >> bit) & 1)
   assert(p2:field(1 << bit)):set_value((state >> (bit + 6)) & 1)
  end
  before = ram:read_u8(0xc002)
  phase = 1
 elseif phase == 1 then phase = 2
 else
  output:write(string.format('%d,%d,%d,%d,%d,%d,%d\n',state,p1:read(),p2:read(),ram:read_u8(0xc000),ram:read_u8(0xc001),before,ram:read_u8(0xc002)))
  state = state + 1
  phase = 0
  if state == 4096 then
   output:close()
   print('CAPTURE_COMPLETE states=4096')
   machine:exit()
   failed = true
  end
 end
end
emu.register_frame_done(function()
 if failed then return end
 local ok,err=pcall(step)
 if not ok then failed=true; output:close(); print('CAPTURE_ERROR '..tostring(err)); machine:exit() end
end)
