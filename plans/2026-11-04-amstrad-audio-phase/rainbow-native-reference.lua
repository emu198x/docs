-- Ordinary firmware/keyboard boot; derived geometry input, no memory writes.
local out=assert(os.getenv("PROBE_OUTPUT"))
local screen=assert(manager.machine.screens[":screen"])
local function shot(name)
 assert(screen:snapshot(out.."/"..name..".png")==nil,"snapshot failed")
end
emu.wait(4.9)
shot("menu")
assert(manager.machine.natkeyboard.can_post,"keyboard unavailable")
manager.machine.natkeyboard:post_coded("{ENTER}")
emu.wait(15.1)
shot("twenty-seconds")
emu.wait(105.35)
shot("coarse-aligned")
local first=screen:frame_number()
for i=0,63 do
 if i>0 then emu.wait(screen.frame_period) end
 assert(screen:frame_number()==first+i,"native field skipped or repeated")
 local name=string.format("%03d",i)
 local pixels,w,h=screen:pixels()
 assert(w==352 and h==296 and #pixels==352*296*4,"unexpected pixels")
 local file=assert(io.open(out.."/"..name..".argb","wb"))
 assert(file:write(pixels))
 assert(file:close())
 shot("phase-"..name)
 print("NATIVE_FRAME "..i.." "..screen:frame_number().." "..emu.time())
end
manager.machine:exit()
