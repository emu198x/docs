// license:BSD-3-Clause
// copyright-holders:Lee Ward, Dirk Best, Curt Coder
uint8_t mtx_state::mtx_sound_strobe_r()
{
	m_sn->write(m_sound_latch);
	return 0xff;
}

void mtx_state::mtx_sound_latch_w(uint8_t data)
{
	m_sound_latch = data;
}
