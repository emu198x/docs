// Run the observation cartridge through Mesen's normal CPU/PPU/mapper path.
// Include real definitions instead of replicating the configuration layout.
#include "Shared/SettingTypes.h"
#include "Shared/MemoryType.h"
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <thread>

extern "C" {
void InitDll();
void InitializeEmu(const char*, void*, void*, bool, bool, bool, bool);
void SetNesConfig(NesConfig);
void SetEmulationFlag(int, bool);
bool LoadRom(char*, char*);
uint8_t GetMemoryValue(int, uint32_t);
void Stop();
void Release();
}

static uint8_t read_ram(uint32_t address) {
    return GetMemoryValue(static_cast<int>(MemoryType::NesMemory), address);
}

int main(int argc, char** argv) {
    if (argc != 3) {
        std::fprintf(stderr, "usage: reference_run MESEN_HOME ROM\n");
        return 2;
    }
    InitDll();
    InitializeEmu(argv[1], nullptr, nullptr, true, true, true, true);
    NesConfig config{};
    config.RamPowerOnState = RamState::AllZeros;
    config.Region = ConsoleRegion::Ntsc;
    SetNesConfig(config);
    SetEmulationFlag(static_cast<int>(EmulationFlags::MaximumSpeed), true);
    char patch[] = "";
    bool ok = LoadRom(argv[2], patch);
    if (ok) {
        for (int poll = 0; poll < 500 && read_ram(0x04f1) != 0xa5; ++poll) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
        ok = read_ram(0x04f0) == 0xa5 && read_ram(0x04f1) == 0xa5 &&
             read_ram(0x04f7) == 32 && read_ram(0x04f2) == 0;
        const char signature[] = "M5C1";
        for (int i = 0; i < 4; ++i) {
            ok = ok && read_ram(0x04f3 + i) == signature[i];
        }
        std::puts("mode,input,same_mode_page,retained_page,complement,repeat");
        for (int row = 0; row < 32; ++row) {
            const int mode = row / 8, input = row % 8;
            const int same = read_ram(0x0420 + row);
            const int retained = read_ram(0x0400 + row);
            const int complement = read_ram(0x0440 + row);
            const int repeat = read_ram(0x0460 + row);
            ok = ok && (retained ^ complement) == 255 && retained == repeat;
            ok = ok && same == (input << (3 - mode)) + (7 >> mode);
            if (mode == 3) ok = ok && retained == input;
            std::printf("%d,%d,%d,%d,%d,%d\n", mode, input, same,
                        retained, complement, repeat);
        }
    }
    Stop();
    Release();
    if (!ok) {
        std::fprintf(stderr, "reference completion, static-page or read control failed\n");
        return 1;
    }
    return 0;
}
