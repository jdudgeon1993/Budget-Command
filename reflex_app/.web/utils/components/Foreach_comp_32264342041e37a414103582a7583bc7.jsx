
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_32264342041e37a414103582a7583bc7 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.forecast_accounts_rx_state_ ?? [],((a_rx_state_,index_3e6347e8fe7010de86b8bbc5e6241a93)=>(jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.forecast_account_rx_state_?.valueOf?.() === a_rx_state_?.["id"]?.valueOf?.()) ? ({ ["padding"] : "4px 10px", ["border_radius"] : "20px", ["cursor"] : "pointer", ["border"] : "1px solid #BF5AF2", ["background"] : "#BF5AF218" }) : ({ ["padding"] : "4px 10px", ["border_radius"] : "20px", ["cursor"] : "pointer", ["border"] : "1px solid rgba(255,255,255,0.08)", ["background"] : "rgba(255,255,255,0.08)", ["_hover"] : ({ ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),key:index_3e6347e8fe7010de86b8bbc5e6241a93,onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_forecast_account", ({ ["aid"] : a_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "6px", ["alignItems"] : "center" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "8px", ["height"] : "8px", ["borderRadius"] : "50%", ["background"] : a_rx_state_?.["color"], ["flexShrink"] : "0" })},),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px" })},a_rx_state_?.["name"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["color"] : ((reflex___state____state__cura___state____app_state.forecast_account_rx_state_?.valueOf?.() === a_rx_state_?.["id"]?.valueOf?.()) ? "#BF5AF2" : "#606088") })},a_rx_state_?.["balance_fmt"]))))))
    )
});
