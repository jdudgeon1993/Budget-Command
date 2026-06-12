
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_23dddd3857f6d6c0aca17bf10088109a = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_f7364dd4fe42d6c00a824ec65f67ee72 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.save_account_settings", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "2", ["padding"] : "9px", ["borderRadius"] : "8px", ["background"] : (reflex___state____state__cura___state____app_state.acct_settings_saving_rx_state_ ? "rgba(255,255,255,0.08)" : "#BF5AF2"), ["color"] : "#fff", ["fontSize"] : "11px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["letterSpacing"] : "0.06em", ["textTransform"] : "uppercase", ["&:hover"] : ({ ["opacity"] : "0.9" }) }),onClick:on_click_f7364dd4fe42d6c00a824ec65f67ee72},children)
    )
});
