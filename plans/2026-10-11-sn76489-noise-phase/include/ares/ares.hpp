#pragma once
// Standalone chip dependency adapter: retain the reference's actual nall
// arithmetic, arrays, serialization and type aliases; omit host UI registration.
#include <nall/nall.hpp>
#include <nall/serializer.hpp>
using namespace nall;
using namespace nall::primitives;
#include <ares/types.hpp>
